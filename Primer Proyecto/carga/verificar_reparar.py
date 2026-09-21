#!/usr/bin/env python3
"""Verificador/reparador idempotente de la BD aerolinea_db.

Esquema confirmado (aerolinea_db):
  * Tablas COUNTER (se reconstruyen con TRUNCATE + UPDATE ...+=):
      - conteo_asientos_por_vuelo_clase  PK (vuelo_id, clase)
          disponibles/ocupados/bloqueados  (estado: disponible/ocupado/bloqueado)
      - ocupacion_por_ruta_mes  PK (ruta, mes, vuelo_id)
          reservas_confirmadas, capacidad   (SOLO counters; NO ingresos)
  * Tablas de DETALLE (ingreso_total como clustering key → NO es counter):
      - ingresos_vuelos_por_mes  PK (mes, ingreso_total, vuelo_id)
          codigo_vuelo  → se reconstruye con TRUNCATE + INSERT (desde pagos)
  * Tablas BASE (PK propia): reservas, pagos_por_reserva, historial_pasajero,
    manifiesto_vuelo (PK (vuelo_id, asiento)).
"""
import argparse
import csv
import os
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from functools import partial

from cassandra import ConsistencyLevel, OperationTimedOut
from cassandra.cluster import Cluster, ConnectionException, NoHostAvailable
from cassandra import ReadTimeout, Unavailable, WriteTimeout

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
DATA = os.path.join(BASE, "data")
ALIAS_CSV = {"asientos_por_vuelo.csv": "asientos_por_vuelo.csv",
             "pagos_por_reserva.csv": "pagos.csv",
             "historial_pasajero.csv": "historial.csv",
             "manifiesto_vuelo.csv": "manifiesto.csv"}

FMT = "%Y-%m-%d %H:%M:%S"
PARSE_DT = lambda s: datetime.strptime(s, FMT) if s else None  # noqa: E731
KS = "aerolinea_db"
ERRORES_TRANSITORIOS = (
    OperationTimedOut, ReadTimeout, Unavailable, WriteTimeout,
    ConnectionException, NoHostAvailable)


def es_transitorio(e: BaseException) -> bool:
    return isinstance(e, ERRORES_TRANSITORIOS)


def leer_csv(nombre: str) -> list[dict]:
    nombre = ALIAS_CSV.get(nombre, nombre)
    with open(os.path.join(DATA, nombre), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", default="127.0.0.1")
    ap.add_argument("--ports", default="9042,9142,9242")
    ap.add_argument("--cl", default="QUORUM")
    args = ap.parse_args()

    contact = [(args.hosts, int(p)) for p in args.ports.split(",")]
    cluster = Cluster(contact_points=contact, connect_timeout=30,
                      control_connection_timeout=30)
    session = cluster.connect(KS)
    session.default_consistency_level = getattr(ConsistencyLevel, args.cl)
    session.default_timeout = 60
    print(f"Conectado (CL={args.cl})")

    def ejecutar(desc: str, fn):
        for _ in range(10):
            try:
                return fn()
            except Exception as e:  # noqa: BLE001
                if not es_transitorio(e):
                    raise
        raise RuntimeError(f"Agotó reintentos: {desc}")

    def contar(tabla: str) -> int:
        return ejecutar(f"COUNT {tabla}",
                        lambda: session.execute(f"SELECT COUNT(*) FROM {KS}.{tabla}").one()[0])

    def rids_en_db(tabla: str, col: str) -> set[int]:
        return ejecutar(f"SELECT {col} FROM {tabla}",
                        lambda: {r[0] for r in session.execute(f"SELECT {col} FROM {KS}.{tabla}")})

    def insertar_simple(stmt, params) -> None:
        for _ in range(8):
            try:
                session.execute(stmt, params)
                return
            except Exception as e:  # noqa: BLE001
                if not es_transitorio(e):
                    raise
        raise RuntimeError(f"No se pudo insertar {params}")

    print("\n[1] Reparando filas faltantes...")
    reservas_csv = {int(r["reserva_id"]): r for r in leer_csv("reservas.csv")}
    pagos_csv = {int(r["reserva_id"]): r for r in leer_csv("pagos_por_reserva.csv")}
    hist_csv = {int(r["reserva_id"]): r for r in leer_csv("historial_pasajero.csv")}
    total_rids = set(reservas_csv) | set(pagos_csv)

    en_res = rids_en_db("reservas", "reserva_id")
    en_pag = rids_en_db("pagos_por_reserva", "reserva_id")
    en_his = rids_en_db("historial_pasajero", "reserva_id")
    faltan_res = total_rids - en_res
    faltan_pag = total_rids - en_pag
    faltan_his = total_rids - en_his

    print(f"  reservas faltantes   : {len(faltan_res)}")
    print(f"  pagos faltantes      : {len(faltan_pag)}")
    print(f"  historial faltantes  : {len(faltan_his)}")

    s_res = session.prepare("INSERT INTO reservas (reserva_id, pasajero_id, vuelo_id, asiento, fecha_reserva, estado) VALUES (?,?,?,?,?,?)")
    s_pag = session.prepare("INSERT INTO pagos_por_reserva (reserva_id, monto, metodo_pago, fecha_pago, estado_pago) VALUES (?,?,?,?,?)")
    s_his = session.prepare("INSERT INTO historial_pasajero (pasajero_id, fecha_reserva, reserva_id, vuelo_id, codigo_vuelo, origen, destino, fecha_salida, asiento, clase, estado_reserva, estado_pago, monto, metodo_pago, fecha_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")

    reparados = 0
    for rid in sorted(faltan_res | faltan_pag | faltan_his):
        if rid in reservas_csv:
            r = reservas_csv[rid]
            insertar_simple(s_res, (rid, int(r["pasajero_id"]), int(r["vuelo_id"]),
                                    r["asiento"], PARSE_DT(r["fecha_reserva"]), r["estado"]))
        if rid in pagos_csv:
            p = pagos_csv[rid]
            insertar_simple(s_pag, (rid, Decimal(p["monto"]), p["metodo_pago"],
                                    PARSE_DT(p["fecha_pago"]), p["estado_pago"]))
        if rid in hist_csv:
            h = hist_csv[rid]
            insertar_simple(s_his, (int(h["pasajero_id"]), PARSE_DT(h["fecha_reserva"]), rid,
                                    int(h["vuelo_id"]), h["codigo_vuelo"], h["origen"],
                                    h["destino"], PARSE_DT(h["fecha_salida"]), h["asiento"],
                                    h["clase"], h["estado_reserva"], h["estado_pago"],
                                    Decimal(h["monto"]), h["metodo_pago"], PARSE_DT(h["fecha_pago"])))
        reparados += 1
    print(f"  {reparados} registros reparados")

    # Manifiesto: reconstrucción POR (vuelo_id, asiento) — la tabla NO tiene
    # reserva_id; su PK es (vuelo_id, asiento). Reconstrucción idempotente.
    print("\n[2] Reconstruyendo manifiesto...")
    session.execute("TRUNCATE manifiesto_vuelo")
    s_man = session.prepare("INSERT INTO manifiesto_vuelo (vuelo_id, asiento, pasajero_id, pasajero_nombre, documento, nacionalidad, clase, estado_reserva, estado_pago) VALUES (?,?,?,?,?,?,?,?,?)")
    for m in leer_csv("manifiesto_vuelo.csv"):
        insertar_simple(s_man, (int(m["vuelo_id"]), m["asiento"], int(m["pasajero_id"]),
                                m["nombre"], m["documento"], m["nacionalidad"],
                                m["clase"], m["estado_reserva"], m["estado_pago"]))
    print(f"  manifiesto reconstruido ({contar('manifiesto_vuelo')} filas)")

    print("\n[3] Reconstruyendo agregados...")

    # Q1: conteo_asientos_por_vuelo_clase (tabla COUNTER)
    session.execute("TRUNCATE conteo_asientos_por_vuelo_clase")
    u_q1 = session.prepare("UPDATE conteo_asientos_por_vuelo_clase SET disponibles=disponibles+?, ocupados=ocupados+?, bloqueados=bloqueados+? WHERE vuelo_id=? AND clase=?")
    q1 = defaultdict(lambda: {"disponibles": 0, "ocupados": 0, "bloqueados": 0})
    EST_COL = {"disponible": "disponibles", "ocupado": "ocupados",
               "bloqueado": "bloqueados"}
    for a in leer_csv("asientos_por_vuelo.csv"):
        k = (int(a["vuelo_id"]), a["clase"])
        q1[k][EST_COL[a["estado"]]] += 1
    for (vid, clase), d in q1.items():
        session.execute(u_q1, (d["disponibles"], d["ocupados"], d["bloqueados"], vid, clase))
    print(f"  Q1 reconstruido ({len(q1)} filas)")

    # Q4: ocupacion_por_ruta_mes (tabla COUNTER) — SOLO counters.
    session.execute("TRUNCATE ocupacion_por_ruta_mes")
    u_q4 = session.prepare("UPDATE ocupacion_por_ruta_mes SET reservas_confirmadas=reservas_confirmadas+?, capacidad=capacidad+? WHERE ruta=? AND mes=? AND vuelo_id=?")
    vuelos = {v.vuelo_id: v for v in session.execute("SELECT vuelo_id, ruta, capacidad, fecha_salida FROM vuelos")}
    reservas_confirmadas = defaultdict(int)
    capac = {}
    for row in session.execute("SELECT vuelo_id, estado FROM reservas"):
        if row.estado != "confirmada":
            continue
        v = vuelos.get(row.vuelo_id)
        if v is None:
            continue
        k = (v.ruta, v.fecha_salida.strftime("%Y-%m"), row.vuelo_id)
        reservas_confirmadas[k] += 1
        capac[k] = v.capacidad
    for (ruta, mes, vid), n in reservas_confirmadas.items():
        session.execute(u_q4, (n, capac[(ruta, mes, vid)], ruta, mes, vid))
    print(f"  Q4 reconstruido ({len(reservas_confirmadas)} filas)")

    # Q5: ingresos_vuelos_por_mes — DETALLE (ingreso_total es clustering) →
    #      TRUNCATE + INSERT agregada desde pagos (idéntico a load_data).
    session.execute("TRUNCATE ingresos_vuelos_por_mes")
    s_q5 = session.prepare("INSERT INTO ingresos_vuelos_por_mes (mes, ingreso_total, vuelo_id, codigo_vuelo) VALUES (?,?,?,?)")
    reserva_vuelo = {r.reserva_id: r.vuelo_id for r in session.execute("SELECT reserva_id, vuelo_id FROM reservas")}
    vuelo_codigo = {v.vuelo_id: v.codigo for v in session.execute("SELECT vuelo_id, codigo FROM vuelos")}
    ingresos = defaultdict(Decimal)
    for row in session.execute("SELECT reserva_id, monto, fecha_pago, estado_pago FROM pagos_por_reserva"):
        if row.estado_pago != "pagado" or row.fecha_pago is None:
            continue
        vid = reserva_vuelo.get(row.reserva_id)
        if vid is None:
            continue
        mes = row.fecha_pago.strftime("%Y-%m")
        ingresos[(mes, vid)] += row.monto
    for (mes, vid), total in sorted(ingresos.items()):
        session.execute(s_q5, (mes, total, vid, vuelo_codigo.get(vid, "")))
    print(f"  Q5 reconstruido ({len(ingresos)} filas)")

    print("\n[4] Conteos finales...")
    for tabla in ("reservas", "pagos_por_reserva", "historial_pasajero",
                  "manifiesto_vuelo", "conteo_asientos_por_vuelo_clase",
                  "ocupacion_por_ruta_mes", "ingresos_vuelos_por_mes"):
        print(f"  {tabla:32s} {contar(tabla):>9,}")

    cluster.shutdown()


if __name__ == "__main__":
    main()
