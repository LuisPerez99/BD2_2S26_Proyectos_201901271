#!/usr/bin/env python3
"""
load_data.py — Carga masiva del dataset generado en el clúster Cassandra.

Estrategia:
  * Tablas base (aeronaves, pasajeros, vuelos, asientos): prepared
    statements + execute_concurrent.
  * Reservas/Pagos/Historial/Manifiesto: BATCH WRITES (UNLOGGED). Cada
    batch agrupa las 3-4 escrituras que componen una reserva (reserva +
    pago + historial + manifiesto) para minimizar round-trips. NO se
    puede mezclar `counter` con estamentos DML normales en un batch, por
    eso las tablas de contadores y de agregación se cargan en un pase
    final separado.
  * Contadores Q1/Q4: UPDATE ...+= delta (una fila por agregado).
  * Q5: INSERT final de (mes, ingreso_total, vuelo) por bucket.
"""
import argparse
import csv
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FMT = "%Y-%m-%d %H:%M:%S"
PARSE_DT = lambda s: datetime.strptime(s, FMT) if s else None  # noqa: E731


def leer_csv(nombre: str) -> list[dict]:
    path = os.path.join(DATA_DIR, nombre)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", default="127.0.0.1")
    ap.add_argument("--ports", default="9042,9142,9242")
    ap.add_argument("--cl", default="ONE", choices=["ONE", "QUORUM", "ALL"])
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    contact = [(args.hosts, int(p)) for p in args.ports.split(",")]
    cl = getattr(ConsistencyLevel, args.cl)

    # Contact points como tuplas (host, puerto). Cada nodo publica su CQL
    # nativo en un puerto distinto del host: 9042, 9142 y 9242. Al listarlos
    # como contact points, el driver queda multi-endpoint y el cliente
    # sobrevive a la caída de cualquiera de ellos (necesario para las
    # pruebas de tolerancia a fallos).
    cluster = Cluster(contact_points=contact,
                      connect_timeout=30, control_connection_timeout=30)
    session = cluster.connect()
    session.default_consistency_level = cl
    session.execute("USE aerolinea_db;")
    print(f"Conectado a {contact}, Consistency {args.cl}")

    # ------------------------------------------------------------------
    # 1) Tablas base
    # ------------------------------------------------------------------
    def insert_many(consulta: str, filas: list[tuple], n: int = 50) -> None:
        stmt = session.prepare(consulta)
        lotes = [filas[i:i + n] for i in range(0, len(filas), n)]
        args_list = []
        for lote in lotes:
            b = BatchStatement(batch_type=BatchType.UNLOGGED)
            for reg in lote:
                b.add(stmt, reg)
            args_list.append(b)
        print(f"  {consulta.split('(')[0].split('.')[-1]} → {len(filas)} filas en {len(args_list)} lotes")
        ejecutar_lotes(args_list)

    def ejecutar_lotes(lotes: list[BatchStatement], reintentos: int = 3) -> int:
        pendientes = lotes
        fallos = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            while pendientes and reintentos > 0:
                reintentos -= 1
                fut_a_lote = {ex.submit(session.execute, b): b for b in pendientes}
                fracasados = []
                for f in as_completed(fut_a_lote):
                    try:
                        f.result()
                    except Exception as e:  # noqa: BLE001
                        fallos += 1
                        fracasados.append(fut_a_lote[f])
                        print(f"  ! fallo (reintento {2-int(reintentos)}): {type(e).__name__}")
                pendientes = fracasados
        return fallos

    print("1) Cargando tablas base...")
    # Aeronaves
    insert_many(
        "INSERT INTO aerolinea_db.aeronaves (aeronave_id, modelo, aerolinea, matricula, capacidad_max) VALUES (?,?,?,?,?)",
        [tuple([
            int(r["aeronave_id"]), r["modelo"], r["aerolinea"], r["matricula"], int(r["capacidad_max"]),
        ]) for r in leer_csv("aeronaves.csv")])
    # Pasajeros (tool en lotes de 100 filas para subir throughput)
    insert_many(
        "INSERT INTO aerolinea_db.pasajeros (pasajero_id, nombre, email, documento, telefono, nacionalidad) VALUES (?,?,?,?,?,?)",
        [tuple([
            int(r["pasajero_id"]), r["nombre"], r["email"], r["documento"], r["telefono"], r["nacionalidad"],
        ]) for r in leer_csv("pasajeros.csv")],
        n=100)
    # Vuelos
    insert_many(
        "INSERT INTO aerolinea_db.vuelos (vuelo_id, codigo, aeronave_id, aeronave_modelo, capacidad, origen, destino, ruta, fecha_salida, fecha_llegada, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [tuple([
            int(r["vuelo_id"]), r["codigo"], int(r["aeronave_id"]), r["aeronave_modelo"],
            int(r["capacidad"]), r["origen"], r["destino"], r["ruta"],
            PARSE_DT(r["fecha_salida"]), PARSE_DT(r["fecha_llegada"]), r["estado"],
        ]) for r in leer_csv("vuelos.csv")])
    # Asientos
    insert_many(
        "INSERT INTO aerolinea_db.asientos_por_vuelo (vuelo_id, asiento, clase, estado) VALUES (?,?,?,?)",
        [tuple([int(r["vuelo_id"]), r["asiento"], r["clase"], r["estado"]]) for r in leer_csv("asientos_por_vuelo.csv")],
        n=200)

    # ------------------------------------------------------------------
    # 2) Reservas + Pagos + Historial + Manifiesto (BATCH WRITES)
    # ------------------------------------------------------------------
    print("2) Cargando reservas con BATCH WRITES...")
    reservas = leer_csv("reservas.csv")
    pagos = {r["reserva_id"]: r for r in leer_csv("pagos.csv")}
    historial = {r["reserva_id"]: r for r in leer_csv("historial.csv")}
    manifiesto = {r["reserva_id"]: r for r in leer_csv("manifiesto.csv")}

    s_reserva = session.prepare(
        "INSERT INTO aerolinea_db.reservas (reserva_id, pasajero_id, vuelo_id, asiento, fecha_reserva, estado) VALUES (?,?,?,?,?,?)")
    s_pago = session.prepare(
        "INSERT INTO aerolinea_db.pagos_por_reserva (reserva_id, monto, metodo_pago, fecha_pago, estado_pago) VALUES (?,?,?,?,?)")
    s_hist = session.prepare(
        "INSERT INTO aerolinea_db.historial_pasajero (pasajero_id, fecha_reserva, reserva_id, vuelo_id, codigo_vuelo, origen, destino, fecha_salida, asiento, clase, estado_reserva, estado_pago, monto, metodo_pago, fecha_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
    s_manif = session.prepare(
        "INSERT INTO aerolinea_db.manifiesto_vuelo (vuelo_id, asiento, pasajero_id, pasajero_nombre, documento, nacionalidad, clase, estado_reserva, estado_pago) VALUES (?,?,?,?,?,?,?,?,?)")

    RESERVAS_POR_BATCH = 6  # 6 reservas → 18-24 estamentos por batch
    lotes_reservas = []
    for i in range(0, len(reservas), RESERVAS_POR_BATCH):
        b = BatchStatement(batch_type=BatchType.UNLOGGED)
        for r in reservas[i:i + RESERVAS_POR_BATCH]:
            rid = r["reserva_id"]
            p = pagos[rid]
            h = historial[rid]
            b.add(s_reserva, (int(rid), int(r["pasajero_id"]), int(r["vuelo_id"]),
                              r["asiento"], PARSE_DT(r["fecha_reserva"]), r["estado"]))
            b.add(s_pago, (int(rid), Decimal(p["monto"]), p["metodo_pago"],
                           PARSE_DT(p["fecha_pago"]), p["estado_pago"]))
            b.add(s_hist, (int(h["pasajero_id"]), PARSE_DT(h["fecha_reserva"]),
                           int(rid), int(h["vuelo_id"]), h["codigo_vuelo"],
                           h["origen"], h["destino"], PARSE_DT(h["fecha_salida"]),
                           h["asiento"], h["clase"], h["estado_reserva"],
                           h["estado_pago"], Decimal(h["monto"]), h["metodo_pago"],
                           PARSE_DT(h["fecha_pago"])))
            if rid in manifiesto:
                m = manifiesto[rid]
                b.add(s_manif, (int(m["vuelo_id"]), m["asiento"], int(m["pasajero_id"]),
                                m["nombre"], m["documento"], m["nacionalidad"],
                                m["clase"], m["estado_reserva"], m["estado_pago"]))
        lotes_reservas.append(b)

    errs = ejecutar_lotes(lotes_reservas)
    print(f"  {len(reservas)} reservas insertadas en {len(lotes_reservas)} batches UNLOGGED ({errs} fallos)")

    # ------------------------------------------------------------------
    # 3) Contadores Q1 y Q4 (no pueden ir en batches con DML normal)
    # ------------------------------------------------------------------
    print("3) Cargando contadores (Q1 y Q4)...")
    s_q1 = session.prepare(
        "UPDATE aerolinea_db.conteo_asientos_por_vuelo_clase SET disponibles = disponibles + ?, ocupados = ocupados + ?, bloqueados = bloqueados + ? WHERE vuelo_id = ? AND clase = ?")
    args_q1 = [
        (int(r["disponibles"]), int(r["ocupados"]), int(r["bloqueados"]),
         int(r["vuelo_id"]), r["clase"])
        for r in leer_csv("counters_q1.csv")]
    fallos = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(session.execute, s_q1, a) for a in args_q1]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                fallos += 1
                print("  ! fallo:", e)
    print(f"  Q1: {len(args_q1)} filas de contador ({fallos} fallos)")

    s_q4 = session.prepare(
        "UPDATE aerolinea_db.ocupacion_por_ruta_mes SET reservas_confirmadas = reservas_confirmadas + ?, capacidad = capacidad + ? WHERE ruta = ? AND mes = ? AND vuelo_id = ?")
    args_q4 = [
        (int(r["reservas_confirmadas"]), int(r["capacidad"]),
         r["ruta"], r["mes"], int(r["vuelo_id"]))
        for r in leer_csv("counters_q4.csv")]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(session.execute, s_q4, a) for a in args_q4]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                fallos += 1
                print("  ! fallo:", e)
    print(f"  Q4: {len(args_q4)} filas de contador ({fallos} fallos)")

    # ------------------------------------------------------------------
    # 4) Agregación Q5 (ingresos por mes/vuelo)
    # ------------------------------------------------------------------
    print("4) Cargando agregación de ingresos (Q5)...")
    s_q5 = session.prepare(
        "INSERT INTO aerolinea_db.ingresos_vuelos_por_mes (mes, ingreso_total, vuelo_id, codigo_vuelo) VALUES (?,?,?,?)")
    args_q5 = [(r["mes"], Decimal(r["ingreso_total"]), int(r["vuelo_id"]), r["codigo_vuelo"])
               for r in leer_csv("ingresos_q5.csv")]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(session.execute, s_q5, a) for a in args_q5]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                fallos += 1
                print("  ! fallo:", e)
    print(f"  Q5: {len(args_q5)} filas de agregación ({fallos} fallos)")

    # ------------------------------------------------------------------
    # 5) Verificación rápida de conteos
    # ------------------------------------------------------------------
    print("5) Conteos finales...")
    for tabla in ("aeronaves", "pasajeros", "vuelos", "asientos_por_vuelo",
                  "reservas", "pagos_por_reserva", "historial_pasajero",
                  "manifiesto_vuelo", "conteo_asientos_por_vuelo_clase",
                  "ocupacion_por_ruta_mes", "ingresos_vuelos_por_mes"):
        n = session.execute(f"SELECT COUNT(*) FROM aerolinea_db.{tabla}").one()[0]
        print(f"  {tabla:32s} {n:>8,}")

    session.shutdown()
    cluster.shutdown()


if __name__ == "__main__":
    sys.exit(main())