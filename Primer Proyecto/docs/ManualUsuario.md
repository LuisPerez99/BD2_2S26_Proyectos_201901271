# Manual de Usuario

## Sistema de Reservas y Boletos Aéreos sobre Apache Cassandra (aerolinea_db)

**Bases de Datos 2 — Proyecto 1** · Clúster de 3 nodos · RF=3 · carné 201901271

---

## 1. Objetivo de este manual

Guía práctica, paso a paso, para **consultar y operar** la base de datos de la
aerolínea (164,234 reservas; 151,244 filas de manifiesto). Incluye: cómo entrar
al clúster, las **5 consultas CQL con ejemplos reales y sus parámetros**, y la
secuencia de instalación/arranque del clúster de 3 nodos.

---

## 2. Conexión al clúster

### 2.1 Prerrequisitos

| Componente | Versión | Uso |
|---|---|---|
| Docker + compose | ≥ 20.10 | Orquestación de nodos |
| Apache Cassandra | 4.1 (imagen `cassandra:4.1`) | Motor de BD |
| Python | ≥ 3.11 | Driver `cassandra-driver` 3.29 |
| Puertos | 9042/9142/9242 (CQL) | `cassandra1/2/3` respectivamente |

### 2.2 Comandos de conexión

```sh
# Estado del anillo (los 3 nodos deben estar en "UN")
docker exec cassandra1 nodetool status aerolinea_db

# Consola CQL interactiva contra el nodo 1
docker exec -it cassandra1 cqlsh -u cassandra -p cassandra

# Con el driver Python (contact points = los 3 nodos)
.venv/bin/python - <<'PY'
from cassandra.cluster import Cluster
c = Cluster(contact_points=["127.0.0.1:9042","127.0.0.1:9142","127.0.0.1:9242"])
s = c.connect("aerolinea_db")
print(s.execute("SELECT COUNT(*) FROM conteo_asientos_por_vuelo_clase").one()[0])
PY
```

---

## 3. Las 5 consultas CQL (Q1–Q5) con ejemplos prácticos

A continuación, cada consulta de negocio, su **CQL real**, un **ejemplo
ejecutado sobre los datos cargados** y el resultado obtenido.

### 3.1 Q1 — Disponibilidad de asientos por clase de un vuelo

**Negocio:** *¿cuántos asientos disponibles/ocupados/bloqueados hay por clase
en el vuelo 23?*

```sql
SELECT clase, disponibles, ocupados, bloqueados
FROM aerolinea_db.conteo_asientos_por_vuelo_clase
WHERE vuelo_id = 23;
```

**Parámetros:** `vuelo_id` (int) — clave de partición.

**Resultado real (fragmento):**

| clase | disponibles | ocupados | bloqueados |
|---|---|---|---|
| economica | 38 | 73 | 1 |
| ejecutiva | 3 | 9 | 0 |
| primera | 3 | 5 | 0 |
| ... | | | |

---

### 3.2 Q2 — Historial de reservas de un pasajero (rango de fechas)

**Negocio:** *historial cronológico del pasajero 204184 entre 2025-01 y
2025-12.*

```sql
SELECT fecha_reserva, reserva_id, codigo_vuelo, origen, destino,
       clase, estado_reserva, estado_pago, monto
FROM aerolinea_db.historial_pasajero
WHERE pasajero_id = 204184
  AND fecha_reserva >= '2025-01-01'
  AND fecha_reserva <= '2025-12-31';
```

**Parámetros:** `pasajero_id` (partición), `fecha_reserva` [min,max]
(clustering) → rango cronológico sin `ALLOW FILTERING`.

**Resultado real (fragmento):** 20 filas del pasajero, ordenadas de la más
reciente a la más antigua (clustering `fecha_reserva DESC`).

---

### 3.3 Q3 — Manifiesto de un vuelo

**Negocio:** *manifiesto del vuelo 1203 ordenado por asiento.*

```sql
SELECT asiento, pasajero_nombre, documento, clase, estado_reserva, estado_pago
FROM aerolinea_db.manifiesto_vuelo
WHERE vuelo_id = 1203;
```

**Parámetros:** `vuelo_id` (partición), orden físico por `asiento` (clustering).

**Resultado real (fragmento):**

| asiento | pasajero_nombre | documento | clase | estado_reserva | estado_pago |
|---|---|---|---|---|---|
| 001A | (pasajero) | (doc) | economica | confirmada | pagado |
| 001B | (pasajero) | (doc) | economica | pendiente | pendiente |
| ... (180 asientos del vuelo, 151,244 en todo el clúster) |

---

### 3.4 Q4 — Ocupación por ruta y mes (porcentaje)

**Negocio:** *¿qué vuelos de la ruta `GUA-PTY` tuvieron reservas en `2026-01`?*

```sql
SELECT mes, vuelo_id, reservas_confirmadas, capacidad
FROM aerolinea_db.ocupacion_por_ruta_mes
WHERE ruta = 'GUA-PTY'
  AND mes = '2026-01';
```

**Parámetros:** `ruta` (partición), `mes` + `vuelo_id` (clustering).

**Resultado real (fragmento):**

| mes | vuelo_id | reservas_confirmadas | capacidad | % ocupación |
|---|---|---|---|---|
| 2026-01 | 1048 | 55 | 132 | 41.7 % |
| 2026-01 | 355 | 204 | 277 | 73.6 % |
| ... (1,200 filas en total) |

---

### 3.5 Q5 — Top-5 de vuelos por ingresos en un mes

**Negocio:** *¿cuáles son los 5 vuelos de mayores ingresos en `2026-07`?*

```sql
SELECT mes, ingreso_total, vuelo_id, codigo_vuelo
FROM aerolinea_db.ingresos_vuelos_por_mes
WHERE mes = '2026-07'
LIMIT 5;
```

**Parámetros:** `mes` (partición), `LIMIT N`; el clustering
(`ingreso_total DESC, vuelo_id`) ya entrega orden descendente **sin
ALLOW FILTERING ni ORDER BY**.

**Resultado real (fragmento):**

| mes | ingreso_total | vuelo_id |
|---|---|---|
| 2026-07 | 52664.67 | 995 |
| 2026-07 | 48898.71 | 80 |
| 2026-07 | 48466.92 | 622 |
| 2026-07 | 48313.90 | 194 |
| 2026-07 | 47796.08 | 172 |

---

## 4. Instalación del clúster (paso a paso)

1. **Levantar los 3 nodos**
   ```sh
   docker compose up -d
   docker exec cassandra1 nodetool status    # 3× UN
   ```
2. **Crear keyspace y tablas**
   ```sh
   cat ddl/01_keyspace.cql ddl/02_schema.cql |
     docker exec -i cassandra1 cqlsh -u cassandra -p cassandra
   ```
3. **Cargar datos base + agregaciones** (164,234 reservas):
   ```sh
   .venv/bin/python carga/load_data.py
   ```
4. **Verificar / reparar (idempotente)**
   ```sh
   .venv/bin/python carga/verificar_reparar.py
   ```
5. **Prueba de fallo de un nodo** (Rúbrica 2.5)
   ```sh
   docker stop cassandra2                      # caída del nodo 2
   # Consultas de prueba (deben seguir respondiendo con CL=ONE y QUORUM)
   docker start cassandra2                     # recuperación
   docker exec cassandra1 nodetool status      # 3× UN de nuevo
   ```

---

## 5. Consistencia y tolerancia a fallos (resultados medidos)

Con el nodo 2 caído (2/3 réplicas activas) se midieron las consultas por
Consistency Level:

| Consistency | Éxitos/Intentos | Motivación |
|---|---|---|
| ONE | 10/10 | Máxima disponibilidad; precisa 1 réplica |
| QUORUM | 10/10 | 2 de 3 réplicas; recomendado (RF=3, tolera 1 nodo) |
| ALL | **0/10** (Unavailable) | Exige las 3 réplicas; queda sin servicio con 1 caído |

**Lección:** la configuración operativa **RF=3 + CL=QUORUM** mantiene el
clúster disponible y consistente ante la caída de un nodo; **ALL** deja de
servir (comportamiento correcto y esperado en Cassandra).

---

## 6. Solución de problemas frecuentes

| Síntoma | Causa / acción |
|---|---|
| `Unable to connect to any servers` | ¿Nodos sin `UN`? `nodetool status`; esperar arranque |
| `UnavailableException (ALL)` | Un nodo caído — usar QUORUM/ONE o reiniciar el nodo |
| `NoHostAvailable` | Puertos 9042/9142/9242 no publicados — `docker ps` |
| Consulta lenta | ¿`ALLOW FILTERING`? Consultar por clave de partición |
| `Row not found` | Ejecutar `carga/verificar_reparar.py` (idempotente) |
