#!/usr/bin/env python3
"""Genera el dataset CSV del sistema de recomendacion de restaurantes."""
import csv
import os
import random
import unicodedata
from datetime import date, timedelta

SEED = 20260001
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

N_USUARIOS = 500
N_RESTAURANTES = 200
N_CHEFS = 100
N_PLATILLOS = 50
N_TIPOS_COCINA = 15

rng = random.Random(SEED)
HOY = date(2026, 10, 1)

NOMBRES = [
    "Ana", "Luis", "Maria", "Carlos", "Sofia", "Jorge", "Lucia", "Miguel", "Elena", "Pedro",
    "Carmen", "Jose", "Laura", "Diego", "Paula", "Andres", "Marta", "Raul", "Isabel", "Fernando",
    "Daniela", "Ricardo", "Patricia", "Alejandro", "Camila", "Sergio", "Valeria", "Oscar", "Natalia", "Ivan",
    "Gabriela", "Hector", "Monica", "Felipe", "Rosa", "Alberto", "Adriana", "Manuel", "Claudia", "Roberto",
]

APELLIDOS = [
    "Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres",
    "Flores", "Rivera", "Gomez", "Diaz", "Cruz", "Morales", "Ortiz", "Gutierrez", "Castillo", "Jimenez",
    "Vargas", "Mendoza", "Rojas", "Silva", "Reyes", "Castro", "Romero", "Herrera", "Medina", "Aguilar",
]

PAISES = [
    "Guatemala", "Mexico", "Colombia", "Argentina", "España", "Peru", "Chile", "Ecuador",
    "Costa Rica", "Estados Unidos", "Italia", "Francia", "Japon", "Brasil", "Uruguay",
]

TIPOS_COCINA = [
    ("Italiana", "Pastas, pizzas y cocina mediterranea de Italia."),
    ("Japonesa", "Sushi, ramen y tecnicas minimalistas japonesas."),
    ("Mexicana", "Tacos, moles y sabores picantes de Mexico."),
    ("China", "Platos salteados, dim sum y cocina regional china."),
    ("India", "Currys, especias y cocina del subcontinente indio."),
    ("Tailandesa", "Equilibrio de dulce, acido, salado y picante."),
    ("Francesa", "Alta cocina, salsas y reposteria francesa."),
    ("Española", "Tapas, paellas y jamon de España."),
    ("Griega", "Cocina mediterranea con aceite de oliva y cordero."),
    ("Peruana", "Ceviches, tiraditos y fusion nikkei."),
    ("Brasileña", "Churrasco, feijoada y cocina amazonica."),
    ("Coreana", "Barbacoa, kimchi y fermentados coreanos."),
    ("Vietnamita", "Pho, rollos frescos y hierbas aromaticas."),
    ("Mediterranea", "Dieta balanceada de mariscos, granos y verduras."),
    ("Americana", "Hamburguesas, parrilla y comfort food."),
]

PLATILLOS = [
    ("Pizza Margarita", 65.0, "Masa fina, tomate y mozzarella fresca."),
    ("Lasaña Boloñesa", 80.0, "Capas de pasta con ragú de res."),
    ("Risotto de Hongos", 95.0, "Arroz cremoso con hongos de temporada."),
    ("Sushi Roll California", 110.0, "Roll con cangrejo, aguacate y pepino."),
    ("Ramen Tonkotsu", 85.0, "Caldo de hueso de cerdo y fideos frescos."),
    ("Tacos al Pastor", 45.0, "Cerdo adobado con piña y cilantro."),
    ("Enchiladas Verdes", 70.0, "Tortillas rellenas con salsa verde."),
    ("Pollo Kung Pao", 75.0, "Pollo salteado con maní y chile."),
    ("Dim Sum Variado", 90.0, "Bocadillos al vapor de varios sabores."),
    ("Curry de Pollo", 78.0, "Pollo en salsa de curry y leche de coco."),
    ("Pad Thai", 82.0, "Fideos de arroz con tamarindo y cacahuate."),
    ("Ratatouille", 88.0, "Verduras provenzales guisadas al horno."),
    ("Coq au Vin", 140.0, "Pollo brasado en vino tinto."),
    ("Paella Valenciana", 150.0, "Arroz con mariscos, pollo y azafrán."),
    ("Tortilla Española", 60.0, "Tortilla de patatas y cebolla."),
    ("Moussaka", 92.0, "Berenjena, carne y salsa bechamel."),
    ("Ceviche Clásico", 85.0, "Pescado fresco en leche de tigre."),
    ("Lomo Saltado", 105.0, "Lomo de res salteado con papas y arroz."),
    ("Feijoada", 98.0, "Guiso de frijoles negros con carnes."),
    ("Churrasco Mixto", 160.0, "Parrillada de cortes de res y cerdo."),
    ("Bibimbap", 76.0, "Arroz con verduras, huevo y gochujang."),
    ("Kimchi Jjigae", 68.0, "Guiso picante de kimchi y cerdo."),
    ("Pho Bo", 72.0, "Sopa de res con hierbas y fideos de arroz."),
    ("Rollos de Primavera", 55.0, "Rollos frescos con vegetales y camarón."),
    ("Hummus con Pita", 48.0, "Pure de garbanzo con pan plano."),
    ("Hamburguesa Clásica", 70.0, "Res, queso, lechuga y tomate."),
    ("Baby Back Ribs", 130.0, "Costillas de cerdo con salsa BBQ."),
    ("Alitas Buffalo", 62.0, "Alitas fritas con salsa picante."),
    ("Ensalada César", 58.0, "Lechuga romana, parmesano y aderezo césar."),
    ("Sopa de Tomate", 42.0, "Crema de tomate con albahaca."),
    ("Tiramisú", 55.0, "Postre de café, mascarpone y cacao."),
    ("Crème Brûlée", 60.0, "Crema francesa con caramelo crujiente."),
    ("Cheesecake de Fresa", 58.0, "Tarta cremosa con coulis de fresa."),
    ("Flan de Caramelo", 40.0, "Flan clásico bañado en caramelo."),
    ("Churros con Chocolate", 45.0, "Churros crujientes con chocolate caliente."),
    ("Gyozas de Cerdo", 66.0, "Empanadillas japonesas a la plancha."),
    ("Tempura Mixta", 84.0, "Mariscos y verduras en tempura ligera."),
    ("Cochinita Pibil", 88.0, "Cerdo marinado en achiote y naranja."),
    ("Chiles Rellenos", 72.0, "Chile poblano relleno de queso."),
    ("Arroz Cantonés", 64.0, "Arroz salteado con huevo y verduras."),
    ("Pato al Hoisin", 155.0, "Pato laqueado con salsa hoisin."),
    ("Gulab Jamun", 46.0, "Dulce indio en almíbar de rosa."),
    ("Satay de Pollo", 74.0, "Brochetas de pollo con salsa de cacahuate."),
    ("Crêpes Suzette", 68.0, "Crepes con naranja y licor."),
    ("Boef Bourguignon", 145.0, "Res brasada en vino y verduras."),
    ("Tzatziki con Pan", 44.0, "Yogur griego con pepino y ajo."),
    ("Anticuchos", 62.0, "Brochetas de corazón con ají."),
    ("Arepa Rellena", 50.0, "Arepa con queso y carne mechada."),
    ("Tom Yum Goong", 90.0, "Sopa tailandesa de camarón y limoncillo."),
    ("Mango Sticky Rice", 52.0, "Arroz glutinoso con mango y coco."),
]

PREFIJOS_REST = [
    "La Trattoria", "Casa", "El Rincón", "Sabor", "Cocina", "Bistró", "Cantina",
    "Mesa", "Fogón", "Raíces", "Delicias", "Brasa", "Huerto", "Rincón", "Terraza",
    "Sabores", "Oasis", "Estancia", "Arcada", "Mirador",
]

SUFIJOS_REST = [
    "del Centro", "Real", "Gourmet", "de la Plaza", "& Co", "Premium", "Tradicional",
    "del Puerto", "Moderno", "Familiar", "Selecto", "de Autor", "Nova", "del Valle", "",
]

PUESTOS = ["Chef Ejecutivo", "Sous Chef", "Chef de Partida", "Jefe de Cocina"]
ESTILOS = ["Clasico", "Fusion", "Vanguardia", "Tradicional", "Autor"]


def slug(texto):
    """Convierte texto en slug ASCII sin espacios."""
    sin = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sin.lower().replace(" ", ".")


def fecha_aleatoria(inicio, fin):
    """Devuelve una fecha ISO entre dos fechas."""
    dias = (fin - inicio).days
    return (inicio + timedelta(days=rng.randint(0, dias))).isoformat()


def escribir_csv(nombre, encabezado, filas):
    """Escribe un CSV con encabezado en la carpeta data/."""
    ruta = os.path.join(DATA_DIR, nombre)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(encabezado)
        w.writerows(filas)
    return len(filas)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    conteos = {}

    # --- Tipos de cocina ---
    tipos = []
    for i, (nombre, desc) in enumerate(TIPOS_COCINA[:N_TIPOS_COCINA], start=1):
        tipos.append((i, nombre, desc))
    conteos["tipos_cocina.csv"] = escribir_csv(
        "tipos_cocina.csv", ["tipo_cocina_id", "nombre", "descripcion"], tipos)

    # --- Usuarios ---
    usuarios = []
    for i in range(1, N_USUARIOS + 1):
        nom = rng.choice(NOMBRES)
        ape = rng.choice(APELLIDOS)
        nombre = f"{nom} {ape}"
        email = f"{slug(nombre)}.{i}@correo.com"
        usuarios.append((i, nombre, email, rng.randint(18, 70), rng.choice(PAISES)))
    conteos["usuarios.csv"] = escribir_csv(
        "usuarios.csv", ["usuario_id", "nombre", "email", "edad", "pais"], usuarios)

    # --- Chefs ---
    chefs = []
    for i in range(1, N_CHEFS + 1):
        nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}"
        fnac = fecha_aleatoria(date(1960, 1, 1), date(1995, 12, 31))
        chefs.append((i, nombre, fnac, rng.choice(PAISES)))
    conteos["chefs.csv"] = escribir_csv(
        "chefs.csv", ["chef_id", "nombre", "fecha_nacimiento", "nacionalidad"], chefs)

    # --- Platillos ---
    platillos = []
    for i, (nombre, precio, desc) in enumerate(PLATILLOS[:N_PLATILLOS], start=1):
        platillos.append((i, nombre, f"{precio:.2f}", desc))
    conteos["platillos.csv"] = escribir_csv(
        "platillos.csv", ["platillo_id", "nombre", "precio", "descripcion"], platillos)

    # --- Restaurantes ---
    rangos = ["Económico", "Moderado", "Caro", "Premium"]
    pesos = [30, 40, 20, 10]
    nombres_usados = set()
    restaurantes = []
    pertenece_a = []
    for i in range(1, N_RESTAURANTES + 1):
        while True:
            nombre = f"{rng.choice(PREFIJOS_REST)} {rng.choice(SUFIJOS_REST)}".strip()
            if nombre not in nombres_usados:
                nombres_usados.add(nombre)
                break
        anio = rng.randint(1970, 2024)
        rango = rng.choices(rangos, weights=pesos, k=1)[0]
        desc = f"Restaurante de cocina variada fundado en {anio}."
        restaurantes.append((i, nombre, anio, rango, desc))
        for tid in rng.sample(range(1, N_TIPOS_COCINA + 1), k=rng.randint(1, 3)):
            pertenece_a.append((i, tid))
    conteos["restaurantes.csv"] = escribir_csv(
        "restaurantes.csv",
        ["restaurante_id", "nombre", "año_apertura", "rango_precios", "descripcion"],
        restaurantes)

    # --- PERTENECE_A ---
    conteos["pertenece_a.csv"] = escribir_csv(
        "pertenece_a.csv", ["restaurante_id", "tipo_cocina_id"], pertenece_a)

    # --- OFRECE (restaurante -> platillo) ---
    factor = {"Económico": 0.8, "Moderado": 1.0, "Caro": 1.4, "Premium": 1.9}
    rango_por_rest = {r[0]: r[3] for r in restaurantes}
    ofrece = []
    for rid in range(1, N_RESTAURANTES + 1):
        for pid in rng.sample(range(1, N_PLATILLOS + 1), k=rng.randint(6, 15)):
            base = float(PLATILLOS[pid - 1][1]) * factor[rango_por_rest[rid]]
            precio = round(base * rng.uniform(0.85, 1.2), 2)
            disponible = rng.random() < 0.9
            ofrece.append((rid, pid, f"{precio:.2f}", str(disponible).lower()))
    conteos["ofrece.csv"] = escribir_csv(
        "ofrece.csv", ["restaurante_id", "platillo_id", "precio", "disponible"], ofrece)

    # --- TRABAJA_EN (chef -> restaurante) ---
    trabaja_en = []
    rest_con_chef = set()
    for cid in range(1, N_CHEFS + 1):
        for rid in rng.sample(range(1, N_RESTAURANTES + 1), k=rng.randint(1, 3)):
            fi = fecha_aleatoria(date(2015, 1, 1), HOY)
            trabaja_en.append((cid, rid, fi, rng.choice(PUESTOS)))
            rest_con_chef.add(rid)
    # Garantiza al menos un chef en cada restaurante
    for rid in range(1, N_RESTAURANTES + 1):
        if rid not in rest_con_chef:
            fi = fecha_aleatoria(date(2015, 1, 1), HOY)
            trabaja_en.append((rng.randint(1, N_CHEFS), rid, fi, rng.choice(PUESTOS)))
    conteos["trabaja_en.csv"] = escribir_csv(
        "trabaja_en.csv", ["chef_id", "restaurante_id", "fecha_inicio", "puesto"], trabaja_en)

    # --- PREPARA (chef -> platillo) ---
    prepara = []
    for cid in range(1, N_CHEFS + 1):
        for pid in rng.sample(range(1, N_PLATILLOS + 1), k=rng.randint(2, 5)):
            prepara.append((cid, pid, rng.choice(ESTILOS), str(rng.random() < 0.3).lower()))
    conteos["prepara.csv"] = escribir_csv(
        "prepara.csv", ["chef_id", "platillo_id", "estilo", "especialidad"], prepara)

    # --- LE_GUSTA (usuario -> tipo de cocina) ---
    le_gusta = []
    for uid in range(1, N_USUARIOS + 1):
        for tid in rng.sample(range(1, N_TIPOS_COCINA + 1), k=rng.randint(1, 4)):
            le_gusta.append((uid, tid, rng.randint(1, 5)))
    conteos["le_gusta.csv"] = escribir_csv(
        "le_gusta.csv", ["usuario_id", "tipo_cocina_id", "nivel_interes"], le_gusta)

    # --- CALIFICÓ (usuario -> restaurante) ---
    califico = []
    comentarios = ["Excelente", "Muy bueno", "Bueno", "Regular", "Volvería", ""]
    for uid in range(1, N_USUARIOS + 1):
        for rid in rng.sample(range(1, N_RESTAURANTES + 1), k=rng.randint(3, 8)):
            punt = rng.choices([1, 2, 3, 4, 5], weights=[4, 8, 18, 35, 35], k=1)[0]
            fecha = fecha_aleatoria(date(2022, 1, 1), HOY)
            comentario = rng.choice(comentarios)
            califico.append((uid, rid, punt, fecha, comentario))
    conteos["califico.csv"] = escribir_csv(
        "califico.csv",
        ["usuario_id", "restaurante_id", "puntuacion", "fecha", "comentario"], califico)

    # --- VISITÓ (usuario -> restaurante) ---
    visito = []
    factor_consumo = {"Económico": 120.0, "Moderado": 280.0, "Caro": 520.0, "Premium": 950.0}
    for uid in range(1, N_USUARIOS + 1):
        for rid in rng.sample(range(1, N_RESTAURANTES + 1), k=rng.randint(4, 10)):
            fecha = fecha_aleatoria(date(2022, 1, 1), HOY)
            base = factor_consumo[rango_por_rest[rid]]
            consumo = round(base * rng.uniform(0.5, 1.6), 2)
            con_reserva = rng.random() < rng.uniform(0.2, 0.8)
            visito.append((uid, rid, fecha, f"{consumo:.2f}", str(con_reserva).lower()))
    conteos["visito.csv"] = escribir_csv(
        "visito.csv",
        ["usuario_id", "restaurante_id", "fecha", "consumo", "con_reserva"], visito)

    # --- ES_AMIGO_DE (red social, bidireccional y conectada) ---
    aristas = set()
    # Camino base que garantiza conectividad
    for u in range(1, N_USUARIOS):
        aristas.add((u, u + 1))
    # Aristas aleatorias adicionales
    objetivo = N_USUARIOS * 5
    while len(aristas) < objetivo:
        a = rng.randint(1, N_USUARIOS)
        b = rng.randint(1, N_USUARIOS)
        if a != b:
            aristas.add((min(a, b), max(a, b)))
    amistad = []
    for a, b in aristas:
        fecha = fecha_aleatoria(date(2018, 1, 1), HOY)
        amistad.append((a, b, fecha))
        amistad.append((b, a, fecha))
    conteos["es_amigo_de.csv"] = escribir_csv(
        "es_amigo_de.csv", ["usuario_id", "amigo_id", "fecha_amistad"], amistad)

    # --- Resumen ---
    print(f"Datos generados en: {os.path.abspath(DATA_DIR)}")
    for archivo, n in conteos.items():
        print(f"  {archivo:20s} {n:>7d} filas")


if __name__ == "__main__":
    main()
