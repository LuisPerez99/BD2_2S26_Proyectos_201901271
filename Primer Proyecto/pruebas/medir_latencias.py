#!/usr/bin/env python3
"""
medir_latencias.py — Fase 5/6: plan de ejecución, latencias y distribución.

Para cada consulta Q1–Q5 de negocio sobre `aerolinea_db`:
  1. Resuelve una clave de ejemplo POBLADA (evita particiones vacías).
  2. Mide N iteraciones de la misma consulta (avg/min/max/p50/p95) con
     el Consistency Level indicado (default QUORUM).
  3. Ejecuta 1 iteración con TRACING y muestra el PLAN DE EJECUCIÓN
     (eventos del trace: qué nodos participan y cuánto tarda cada paso).
  4. Verifica la DISTRIBUCIÓN de datos entre nodos:
       - nodetool status        (estado del anillo)
       - nodetool getendpoints  (qué réplicas poseen cada partición)
       - nodetool tablestats    (espacio usado por tabla en cada nodo)

Ejecución:
  .venv/bin/python pruebas/medir_latencias.py --iter 100 --cl QUORUM
"""
import argparse
import math
import statistics
import subprocess
import time

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

KS = "aerolinea_db"


def nodetool(args: str, nodo: str = "cassandra1") -> str:
    try:
        out = subprocess.run(
            ["docker", "exec", nodo, "nodetool"] + args.split(),
            capture_output=True, text=True, timeout=60)
        return out.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"[nodetool no disponible: {type(e).__name__}]"


def medir(session, stmt, params, n):
    lat = []
    for _ in range(n):
        t0 = time.perf_counter()
        rs = session.execute(stmt, params)
        lat.append((time.perf_counter() - t0) * 1000)
        if len(rs.current_rows) == 0:
            pass  # partición vacía: sigue siendo 1 lectura de partición
    lat.sort()
    p50 = lat[len(lat) // 2] if n % 2 else (lat[n // 2 - 1] + lat[n // 2]) / 2
    p95 = lat[min(len(lat) - 1, int(len(lat) * 0.95))]
    return {
        "filas": rs.current_rows and len(rs.current_rows),
        "min": min(lat), "max": max(lat),
        "avg": sum(lat) / len(lat), "p50": p50, "p95": p95,
        "n": len(lat),
    }


def trazar(session, stmt, params):
    """Ejecuta con TRACING y devuelve eventos del plan de ejecución."""
    rs = session.execute(stmt, params, trace=True)
    trace = rs.get_query_trace()
    if trace is None:
        return "  [trace no disponible]"
    lineas = [f"  coordenador={trace.coordinator} duración={trace.duration.total_seconds() * 1e6:.0f} µs"]
    for ev in trace.events:
        lineas.append(f"    {ev.source_elapsed.total_seconds() * 1e6:>12.0f}µs  {ev.source:<15} {ev.description}")
    return "\n".join(lineas)


def ejemplo(session, cql):
    rs = session.execute(SimpleStatement(cql, fetch_size=5))
    return rs.one()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", default="127.0.0.1")
    ap.add_argument("--ports", default="9042,9142,9242")
    ap.add_argument("--cl", default="QUORUM", choices=["ONE", "QUORUM", "ALL"])
    ap.add_argument("--iter", type=int, default=100)
    args = ap.parse_args()

    contact = [(args.hosts, int(p)) for p in args.ports.split(",")]
    cluster = Cluster(contact_points=contact, connect_timeout=30,
                      control_connection_timeout=30)
    session = cluster.connect(KS)
    session.default_consistency_level = getattr(ConsistencyLevel, args.cl)
    print(f"Conectado a {contact} · CL={args.cl} · iter={args.iter}")

    # --- Resolver claves de ejemplo pobladas ---------------------------
    v1 = ejemplo(session, "SELECT vuelo_id FROM conteo_asientos_por_vuelo_clase LIMIT 1")
    vuelo_q1 = int(v1[0])
    v2 = ejemplo(session, "SELECT pasajero_id FROM historial_pasajero LIMIT 1")
    pasajero_q2 = int(v2[0])
    v3 = ejemplo(session, "SELECT vuelo_id FROM manifiesto_vuelo LIMIT 1")
    vuelo_q3 = int(v3[0])
    v4 = ejemplo(session, "SELECT ruta, mes FROM ocupacion_por_ruta_mes LIMIT 1")
    ruta_q4, mes_q4 = str(v4[0]), v4[1]
    v5 = ejemplo(session, "SELECT mes FROM ingresos_vuelos_por_mes LIMIT 1")
    mes_q5 = str(v5[0])

    QUERIES = [
        ("Q1", "Disponibilidad de asientos por clase",
         "SELECT clase, disponibles, ocupados, bloqueados "
         "FROM conteo_asientos_por_vuelo_clase WHERE vuelo_id = ?",
         [vuelo_q1], f"vuelo={vuelo_q1}"),
        ("Q2", "Historial cronológico de un pasajero (rango de fechas)",
         "SELECT fecha_reserva, reserva_id, codigo_vuelo, origen, destino, "
         "clase, estado_reserva, estado_pago, monto "
         "FROM historial_pasajero "
         "WHERE pasajero_id = ? AND fecha_reserva >= '2026-01-01' "
         "AND fecha_reserva <= '2026-12-31'",
         [pasajero_q2], f"pasajero={pasajero_q2} 2026"),
        ("Q3", "Manifiesto de vuelo enriquecido (por asiento)",
         "SELECT asiento, pasajero_nombre, documento, clase, estado_reserva, "
         "estado_pago FROM manifiesto_vuelo WHERE vuelo_id = ?",
         [vuelo_q3], f"vuelo={vuelo_q3}"),
        ("Q4", "Ocupación % por ruta y rango de meses",
         "SELECT mes, vuelo_id, reservas_confirmadas, capacidad "
         "FROM ocupacion_por_ruta_mes WHERE ruta = ? AND mes >= ? AND mes <= '2026-12'",
         [ruta_q4, mes_q4], f"ruta={ruta_q4} mes={mes_q4}"),
        ("Q5", "Top-5 de vuelos por ingresos",
         "SELECT mes, ingreso_total, vuelo_id, codigo_vuelo "
         "FROM ingresos_vuelos_por_mes WHERE mes = ? LIMIT 5",
         [mes_q5], f"mes={mes_q5}"),
    ]

    # --- 1) Latencias + 2) Plan de ejecución (TRACE) -------------------
    print("\n== Latencias (ms) por consulta ==")
    print(f"{'ID':<4}{'CL':<7}{'iter':<6}{'filas':<7}{'avg':>8}{'p50':>8}{'p95':>8}{'min':>8}{'max':>8}")
    resultados = []
    for qid, nombre, cql, params, muestra in QUERIES:
        pstmt = session.prepare(cql)
        r = medir(session, pstmt, params, args.iter)
        resultados.append((qid, nombre, pstmt, params, muestra, r))
        print(f"{qid:<4}{args.cl:<7}{r['n']:<6}{r['filas'] or 0:<7}"
              f"{r['avg']:>8.2f}{r['p50']:>8.2f}{r['p95']:>8.2f}"
              f"{r['min']:>8.2f}{r['max']:>8.2f}")
        print(f"     muestra: {muestra}")

    print("\n== Plan de ejecución (TRACING, 1 iteración por query) ==")
    for qid, nombre, pstmt, params, muestra, _ in resultados:
        print(f"\n[{qid}] {nombre} · {muestra}")
        print(trazar(session, pstmt, params))

    # --- 3) Distribución entre nodos -----------------------------------
    print("\n== Distribución de datos entre nodos ==")
    print("\n-- nodetool status --")
    print(nodetool("status"))

    print("\n-- getendpoints (réplicas por partición) --")
    partes = [
        ("reservas", "1"),
        ("historial_pasajero", str(pasajero_q2)),
        ("manifiesto_vuelo", str(vuelo_q3)),
        ("conteo_asientos_por_vuelo_clase", str(vuelo_q1)),
        ("ocupacion_por_ruta_mes", ruta_q4),
        ("ingresos_vuelos_por_mes", mes_q5),
    ]
    for tabla, clave in partes:
        out = nodetool(f"getendpoints aerolinea_db {tabla} {clave}")
        print(f"  {tabla:<32} partición {clave:<6} → {out}")

    print("\n-- tablestats por nodo (espacio usado) --")
    for nodo in ("cassandra1", "cassandra2", "cassandra3"):
        out = nodetool("tablestats aerolinea_db.reservas", nodo)
        for linea in out.splitlines():
            if "Space used" in linea:
                print(f"  {nodo}: {linea.strip()}")

    cluster.shutdown()


if __name__ == "__main__":
    main()