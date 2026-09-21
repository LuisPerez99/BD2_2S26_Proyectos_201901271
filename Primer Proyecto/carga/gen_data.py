#!/usr/bin/env python3
"""
gen_data.py — Generador de datos sintéticos del sistema de reservas aéreas.

Genera el dataset completo en CSV dentro de `data/`:
  aeronaves, pasajeros, vuelos, asientos_por_vuelo, reservas, pagos,
  historial_pasajero, manifiesto_vuelo, y los agregados para las tablas
  especializadas (counters Q1/Q4 y agregación Q5).

Reproducible: se siembran `random` y `Faker` con el carnet como seed.
"""
import csv
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker

SEED = 201901271
MONTHS = 9                                   # ene-sep 2026
START = datetime(2026, 1, 1)
N_AERONAVES = 30
N_PASAJEROS = 25_000
N_VUELOS = 1_200
TARGET_RESERVAS = 120_000
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

rng = random.Random(SEED)
fake = Faker("es_ES")
fake.seed_instance(SEED)

AEROLINEA = "AeroGuate S.A."

# Modelos de aeronave -> (capacidad, abreviaturas de clase)
MODELOS = [
    ("A319", 132), ("A320", 180), ("A321", 220),
    ("B737-800", 189), ("B757-200", 200), ("A330-300", 277),
    ("B777-300ER", 368), ("E190", 98),
]

# Rutas (origen, destino, peso de demanda relativo, duración aprox. en horas)
RUTAS = [
    ("GUA", "SAL", 1.0, 1), ("SAL", "GUA", 1.0, 1),
    ("GUA", "MEX", 0.9, 2), ("MEX", "GUA", 0.9, 2),
    ("GUA", "MIA", 0.8, 2), ("MIA", "GUA", 0.8, 2),
    ("GUA", "MAD", 0.5, 10), ("MAD", "GUA", 0.5, 10),
    ("GUA", "BOG", 0.4, 3), ("BOG", "GUA", 0.4, 3),
    ("GUA", "PTY", 0.4, 2), ("PTY", "GUA", 0.4, 2),
    ("MEX", "MIA", 0.6, 3), ("MIA", "MEX", 0.6, 3),
    ("SAL", "MEX", 0.5, 2), ("MEX", "SAL", 0.5, 2),
    ("MEX", "MAD", 0.4, 10), ("MAD", "MEX", 0.4, 10),
    ("BOG", "MAD", 0.3, 9), ("MAD", "BOG", 0.3, 9),
    ("MIA", "MAD", 0.3, 8), ("MAD", "MIA", 0.3, 8),
    ("GUA", "SJO", 0.3, 3), ("SJO", "GUA", 0.3, 3),
    ("GUA", "CUN", 0.3, 2), ("CUN", "GUA", 0.3, 2),
    ("PTY", "MIA", 0.3, 3), ("MIA", "PTY", 0.3, 3),
    ("LIM", "BOG", 0.3, 3), ("BOG", "LIM", 0.3, 3),
    ("BOG", "PTY", 0.3, 2), ("PTY", "BOG", 0.3, 2),
    ("GUA", "LAX", 0.2, 5), ("MIA", "JFK", 0.3, 3),
    ("JFK", "MIA", 0.3, 3), ("MEX", "JFK", 0.3, 5),
]
RUTAS_WEIGHTS = [r[2] for r in RUTAS]

# Tarifas mín/máx (USD) por clase: clase -> (min, max)
TARIFAS = {
    "economica": (120, 460),
    "ejecutiva": (390, 900),
    "primera":   (800, 1500),
}

METODOS_PAGO = ["tarjeta", "tarjeta", "transferencia", "transferencia", "efectivo"]

NACIONALIDADES = [
    "guatemalteca", "salvadoreña", "mexicana", "española",
    "colombiana", "panameña", "peruana", "estadounidense",
]

# Formato de fecha usado en los CSV (naive UTC)
FMT = "%Y-%m-%d %H:%M:%S"


def fmt(dt: datetime | None) -> str:
    return dt.strftime(FMT) if dt is not None else ""


def cabina_por_modelo(capacidad: int) -> list[tuple[int, str, str]]:
    """
    Devuelve el mapa de cabina de un modelo: lista de
    (fila, clase, letras) que suma exactamente `capacidad`.
    Primera: 2 filas x4; ejecutiva: ~12% restante x4; resto económica x6.
    """
    filas: list[tuple[int, str, str]] = []
    restante = capacidad
    fila = 1
    # Primera clase: 2 filas, 4 abreast (A-D)
    for _ in range(2):
        filas.append((fila, "primera", "ABCD"))
        fila += 1
        restante -= 4
    # Ejecutiva: filas de 4 (A-D) hasta cubrir ~12% del resto
    ej_seats = max(4, (restante * 12) // 100)
    ej_rows = ej_seats // 4
    for _ in range(ej_rows):
        filas.append((fila, "ejecutiva", "ABCD"))
        fila += 1
        restante -= 4
    # Económica: filas de 6 (A-F), la última puede llevar "menos" letras
    while restante > 0:
        letras = "ABCDEF"[: min(6, restante)]
        filas.append((fila, "economica", letras))
        fila += 1
        restante -= len(letras)
    return filas


def generaaeronaves() -> list[dict]:
    aeronaves = []
    for i in range(1, N_AERONAVES + 1):
        modelo, cap = MODELOS[i % len(MODELOS)]
        matricula = "%s%s%d" % (rng.choice(["N", "GT-", "XA-"]), rng.choice("ABC"), rng.randint(100, 999))
        aeronaves.append({
            "aeronave_id": i,
            "modelo": modelo,
            "aerolinea": AEROLINEA,
            "matricula": matricula,
            "capacidad_max": cap,
        })
    return aeronaves


def generapasajeros() -> list[dict]:
    pasajeros = []
    for i in range(1, N_PASAJEROS + 1):
        nombre = (fake.first_name() + " " + fake.last_name() + " " + fake.last_name()).strip()
        docu = fake.bothify("????-#####") if rng.random() < 0.5 else str(rng.randint(1000000000000, 1999999999999))
        pasajeros.append({
            "pasajero_id": i,
            "nombre": nombre,
            "email": fake.free_email(),
            "documento": docu,
            "telefono": rng.choice(["+502 ", "+503 ", "+52 "]) + str(rng.randint(30000000, 79999999)),
            "nacionalidad": rng.choice(NACIONALIDADES),
        })
    return pasajeros


def generavuelos(aeronaves: list[dict]) -> list[dict]:
    vuelos = []
    dias_por_mes = 30
    modelos = {a["aeronave_id"]: a for a in aeronaves}
    for vid in range(1, N_VUELOS + 1):
        o, d, _w, horas = rng.choices(RUTAS, weights=RUTAS_WEIGHTS, k=1)[0]
        mes = rng.randrange(MONTHS)
        dia = rng.randint(1, dias_por_mes)
        hora = rng.randint(5, 22)
        salida = START + timedelta(days=mes * 30 + dia - 1, hours=hora, minutes=rng.randint(0, 59))
        llegada = salida + timedelta(hours=horas, minutes=rng.randint(0, 20))
        aeronave = modelos[rng.randint(1, len(aeronaves))]
        # Estado según si el vuelo ya ocurrió (hoy = 2026-09-21 de este lab)
        if salida > datetime(2026, 9, 21, 12, 0, 0):
            estado = rng.choices(["programado", "retrasado"], weights=[0.92, 0.08])[0]
        else:
            estado = rng.choices(["completado", "cancelado", "retrasado"], weights=[0.9, 0.06, 0.04])[0]
        vuelos.append({
            "vuelo_id": vid,
            "codigo": "AV%04d" % (vid + 100),
            "aeronave_id": aeronave["aeronave_id"],
            "aeronave_modelo": aeronave["modelo"],
            "capacidad": aeronave["capacidad_max"],
            "origen": o,
            "destino": d,
            "ruta": "%s-%s" % (o, d),
            "fecha_salida": salida,
            "fecha_llegada": llegada,
            "estado": estado,
        })
    return vuelos


def tarifa(clase: str) -> Decimal:
    lo, hi = TARIFAS[clase]
    return Decimal(str(round(rng.uniform(lo, hi), 2)))


def genera_reservas(vuelos: list[dict], pasajeros: list[dict]) -> dict:
    """
    Genera reservas + pagos + histogramas para las tablas especializadas.
    Devuelve dict con listas de filas por CSV.
    """
    by_id = {p["pasajero_id"]: p for p in pasajeros}
    filas_reservas = []
    filas_pagos = []
    filas_historial = []
    filas_manifiesto = []
    filas_q1 = []        # (vuelo, clase) -> [disp, ocup, bloqueados]
    filas_q4 = {}        # (ruta, mes, vuelo) -> [res_confirmadas, capacidad]
    filas_q5 = {}        # (mes_pago, vuelo) -> ingreso total
    filas_asientos = []

    rid = 0
    total = 0

    for vuelo in vuelos:
        vid = vuelo["vuelo_id"]
        cap = vuelo["capacidad"]
        filas = cabina_por_modelo(cap)
        # Construye la lista de todos los asientos del vuelo
        asientos = []
        for fila, clase, letras in filas:
            for ch in letras:
                asientos.append((fila, clase, "%03d%s" % (fila, ch)))
        # Bloquear 0-2 asientos al azar (mantenimiento)
        bloqueados = rng.sample([a for a in asientos], k=rng.randint(0, 2)) if asientos else []
        bloqueados_set = set(id(b) for b in bloqueados)
        reservables = [a for a in asientos if id(a) not in bloqueados_set]

        # Ocupación objetivo del vuelo
        ocupacion = rng.uniform(0.45, 0.85)
        n_res = int(len(reservables) * ocupacion)
        elegidos = rng.sample(reservables, k=n_res)

        estado_por_asiento = {a[2]: ("bloqueado" if id(a) in bloqueados_set else "disponible") for a in asientos}
        vuelo_es_futuro = vuelo["fecha_salida"] > datetime(2026, 9, 21, 12, 0, 0)

        # Resumen contadores Q1 por clase
        q1 = {}
        q4key = (vuelo["ruta"], vuelo["fecha_salida"].strftime("%Y-%m"), vid)
        q4 = filas_q4.setdefault(q4key, [0, cap])

        for fila, clase, asiento in elegidos:
            pasajero = by_id[rng.randint(1, len(pasajeros))]
            # días antes de la salida en que se reservó (1-60)
            dias_antes = rng.randint(1, 60)
            if dias_antes >= (vuelo["fecha_salida"] - datetime(2026, 1, 1)).days + 1:
                dias_antes = max(1, (vuelo["fecha_salida"] - datetime(2026, 1, 1)).days)
            fecha_reserva = vuelo["fecha_salida"] - timedelta(days=dias_antes, minutes=rng.randint(0, 1439))

            # Estado de la reserva según políticas
            if vuelo_es_futuro and rng.random() < 0.20:
                estado_reserva = "pendiente"
            elif rng.random() < 0.08:
                estado_reserva = "cancelada"
            else:
                estado_reserva = "confirmada"

            estado_pago = {"confirmada": "pagado", "pendiente": "pendiente", "cancelada": "reembolsado"}[estado_reserva]
            monto = tarifa(clase)
            fecha_pago = None
            if estado_pago == "pagado":
                fecha_pago = fecha_reserva + timedelta(hours=rng.randint(1, 48))
            elif estado_pago == "reembolsado":
                fecha_pago = fecha_reserva + timedelta(days=2)

            metodo = rng.choice(METODOS_PAGO)

            rid += 1
            total += 1
            estado_por_asiento[asiento] = "ocupado"

            # Historial Q1 por clase
            cl = q1.setdefault(clase, [0, 0, 0])
            cl[1] += 1                      # ocupados

            # Q4: solo confirmadas cuentan para ocupación (sobreventa)
            if estado_reserva == "confirmada":
                q4[0] += 1

            # Q5: ingreso solo de pagos concretados
            if estado_pago == "pagado":
                mes_pago = fecha_pago.strftime("%Y-%m")
                key5 = (mes_pago, vid)
                filas_q5[key5] = filas_q5.get(key5, Decimal("0")) + monto

            filas_reservas.append({
                "reserva_id": rid, "pasajero_id": pasajero["pasajero_id"],
                "vuelo_id": vid, "asiento": asiento,
                "fecha_reserva": fecha_reserva, "estado": estado_reserva,
            })
            filas_pagos.append({
                "reserva_id": rid, "monto": monto, "metodo_pago": metodo,
                "fecha_pago": fecha_pago, "estado_pago": estado_pago,
            })
            filas_historial.append({
                "pasajero_id": pasajero["pasajero_id"], "fecha_reserva": fecha_reserva,
                "reserva_id": rid, "vuelo_id": vid, "codigo_vuelo": vuelo["codigo"],
                "origen": vuelo["origen"], "destino": vuelo["destino"],
                "fecha_salida": vuelo["fecha_salida"], "asiento": asiento,
                "clase": clase, "estado_reserva": estado_reserva,
                "estado_pago": estado_pago, "monto": monto,
                "metodo_pago": metodo, "fecha_pago": fecha_pago,
            })
            # Manifiesto: solo vuelos con reserva activa (confirmada/pendiente)
            if estado_reserva in ("confirmada", "pendiente"):
                filas_manifiesto.append({
                    "reserva_id": rid,
                    "vuelo_id": vid, "asiento": asiento,
                    "pasajero_id": pasajero["pasajero_id"],
                    "nombre": pasajero["nombre"], "documento": pasajero["documento"],
                    "nacionalidad": pasajero["nacionalidad"], "clase": clase,
                    "estado_reserva": estado_reserva, "estado_pago": estado_pago,
                })

        # Cierra los asientos del vuelo
        for fila, clase, asiento in asientos:
            filas_asientos.append({
                "vuelo_id": vid, "asiento": asiento,
                "clase": clase, "estado": estado_por_asiento[asiento],
            })
        # Q1: disponibles por clase = total de clase - ocupados(-bloqueados)
        for clase, datos in q1.items():
            clase_list = [a for a in asientos if a[1] == clase]
            n_bloqueados = sum(1 for a in clase_list if id(a) in bloqueados_set)
            n_ocupados = datos[1]
            n_disponibles = len(clase_list) - n_ocupados - n_bloqueados
            filas_q1.append({
                "vuelo_id": vid, "clase": clase,
                "disponibles": n_disponibles, "ocupados": n_ocupados,
                "bloqueados": n_bloqueados,
            })

    filas_q4_list = [{"ruta": k[0], "mes": k[1], "vuelo_id": k[2],
                      "reservas_confirmadas": v[0], "capacidad": v[1]}
                     for k, v in filas_q4.items()]
    filas_q5_list = [{"mes": k[0], "ingreso_total": v, "vuelo_id": k[1],
                      "codigo_vuelo": next(x["codigo"] for x in vuelos if x["vuelo_id"] == k[1])}
                     for k, v in filas_q5.items()]

    return {
        "asientos": filas_asientos,
        "reservas": filas_reservas,
        "pagos": filas_pagos,
        "historial": filas_historial,
        "manifiesto": filas_manifiesto,
        "q1": filas_q1,
        "q4": filas_q4_list,
        "q5": filas_q5_list,
        "total_reservas": total,
    }


def write_csv(nombre: str, filas: list[dict]) -> None:
    with open(os.path.join(DATA_DIR, nombre), "w", newline="") as f:
        if not filas:
            f.write("")
            return
        campos = list(filas[0].keys())
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in filas:
            row = dict(r)
            for k, v in row.items():
                if isinstance(v, datetime):
                    row[k] = fmt(v)
                elif isinstance(v, Decimal):
                    row[k] = str(v)
            w.writerow(row)


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generando aeronaves...")
    aeronaves = generaaeronaves()
    write_csv("aeronaves.csv", aeronaves)
    print("Generando pasajeros...")
    pasajeros = generapasajeros()
    write_csv("pasajeros.csv", pasajeros)
    print("Generando vuelos...")
    vuelos = generavuelos(aeronaves)
    write_csv("vuelos.csv", vuelos)
    print("Generando reservas/pagos/manifiestos/historial y agregados...")
    datos = genera_reservas(vuelos, pasajeros)
    write_csv("asientos_por_vuelo.csv", datos["asientos"])
    write_csv("reservas.csv", datos["reservas"])
    write_csv("pagos.csv", datos["pagos"])
    write_csv("historial.csv", datos["historial"])
    write_csv("manifiesto.csv", datos["manifiesto"])
    write_csv("counters_q1.csv", datos["q1"])
    write_csv("counters_q4.csv", datos["q4"])
    write_csv("ingresos_q5.csv", datos["q5"])
    print("Total reservas generadas:", datos["total_reservas"])
    print("Archivos en", os.path.abspath(DATA_DIR))


if __name__ == "__main__":
    main()