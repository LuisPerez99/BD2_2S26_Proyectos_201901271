# Manual de Usuario

## Sistema de Reservas y Boletos Aéreos sobre Apache Cassandra (aerolinea_db)

**Nombre:** Luis Pedro Pérez Monzón

**Carné:** 201901271

---

## 1. Introducción

Este manual explica cómo **consultar** la base de datos distribuida de la
aerolínea y cómo **instalar y operar** el clúster Apache Cassandra de 3 nodos
que la sostiene. Está pensado para el personal de TI y de operaciones, e
incluye: las **5 consultas CQL** implementadas con ejemplos reales y sus
parámetros, la guía **paso a paso** de instalación y arranque del clúster, la
carga de datos, la verificación/reparación y la solución de problemas
frecuentes.

---

## 2. Requisitos del sistema

| Componente | Versión / especificación |
|---|---|
| Docker / Docker Compose | ≥ 20.10 / ≥ 2.20 |
| Imagen Cassandra | `cassandra:4.1` |
| Python | ≥ 3.11 con `cassandra-driver` 3.29 |
| Sistema | Linux, macOS o Windows (WSL2) |
| RAM recomendada | ≥ 10 GB (3 nodos Apache Cassandra) |
| Puertos CQL | 9042 (nodo1), 9142 (nodo2), 9242 (nodo3) |

---

## 3. Guía de instalación del clúster (paso a paso)

### 3.1 Levantar los 3 nodos

```sh
git clone <tu-repositorio> && cd "Primer Proyecto"
docker compose up -d
```

### 3.2 Verificar que el clúster esté sano

```sh
docker exec cassandra1 nodetool status
# Debes ver 3 filas con estado UN (Up / Normal):
#   UN  172.0.0.x  36 MiB  16  100.0%  racks=1  27a...  rack1
#   UN  172.0.0.x  36 MiB  16  100.0%  ...      rack1
#   UN  172.0.0.x  36 MiB  16  100.0%  ...      rack1
```

El anillo debe mostrar **los tres nodos `UN`** antes de continuar. Un nodo en
`DN` (Down) o `UJ` (Joining) indica que faltó tiempo de arranque — espera
45–60 s y vuelve a ejecutar `nodetool status`.

### 3.3 Aplicar schema (keyspace + tablas)

```sh
docker exec -i cassandra1 cqlsh -f <(cat ddl/*.cql)
```

### 3.4 Cargar los datos

```sh
.venv/bin/python carga/load_data.py            # 164,234 reservas (batch)
.venv/bin/python carga/verificar_reparar.py     # verificación + reparación
```

---

## 4. Las 5 consultas CQL: ejemplos prácticos

### 4.1 Q1 — Disponibilidad de asientos por clase de un vuelo

**Negocio:** *¿cuántos asientos disponibles/ocupados/bloqueados hay por clase
en el vuelo 442?*

```sql
SELECT clase, disponibles, ocupados, bloqueados
FROM aerolinea_db.conteo_asientos_por_vuelo_clase
WHERE vuelo_id = 442;
```

**Parámetros:** `vuelo_id` (obligatorio, partition key).

**Ejemplo con resultado real (vuelo 501):**

| clase | disponibles | ocupados | bloqueados |
|---|---|---|---|
| economica | 909 | 1,216 | 260 |
| ejecutiva | 64 | 93 | 552 |
| primera | 32 | 30 | 359 |

**Uso en el sistema:** la tabla es `COUNTER`; cada reserva/cancelación
actualiza `disponibles += n`. No requiere `ALLOW FILTERING`.

---

### 4.2 Q2 — Historial cronológico de un pasajero

**Negocio:** *historial del pasajero 75 entre 2025-01-01 y 2025-12-31.*

```sql
SELECT fecha_reserva, reserva_id, codigo_vuelo, origen, destino,
       fecha_salida, asiento, clase, estado_reserva, estado_pago, monto
FROM aerolinea_db.historial_pasajero
WHERE pasajero_id = 75
  AND fecha_reserva >= '2025-01-01'
  AND fecha_reserva <= '2025-12-31';
```

**Parámetros:** `pasajero_id` (partición), rango `fecha_reserva`
(clustering). Devuelve el historial **ordenado cronológico** (DESC) sin
reescribir resultados en el cliente.

---

### 4.3 Q3 — Manifiesto de un vuelo

**Negocio:** *manifiesto del vuelo 1203 de la aeronave en vuelo energizado.*

```sql
SELECT asiento, pasajero_id, pasajero_nombre, documento,
       clase, estado_reserva, estado_pago
FROM aerolinea_db.manifiesto_vuelo
WHERE vuelo_id = 1203;
```

**Parámetros:** `vuelo_id` (partición). Resultado ordenado por numero de
asiento (clustering `asiento`).

---

### 4.4 Q4 — Ocupación por ruta y rango de meses

**Negocio:** *porcentaje de ocupación de la ruta GUA-PTY entre 2026-01 y
2026-06.*

```sql
SELECT mes, vuelo_id, reservas_confirmadas, capacidad
FROM aerolinea_db.ocupacion_por_ruta_mes
WHERE ruta = 'GUA-PTY'
  AND mes >= '2026-01' AND mes <= '2026-06';
```

**Parámetros:** `ruta` (partición), rango `mes` (clustering).

**Resultado real (fragmento):**

| mes | vuelo_id | reservas_confirmadas | capacidad | % ocupación |
|---|---|---|---|---|
| 2026-01 | 557 | 57 | 167 | 34.1% |
| 2026-01 | 953 | 57 | 137 | 41.6% |
| ... | | | | |

---

### 4.5 Q5 — Top 5 de vuelos por ingresos en un mes

**Negocio:** *¿cuáles son los 5 vuelos de mayores ingresos en 2026-07?*

```sql
SELECT mes, ingreso_total, vuelo_id, codigo_vuelo
FROM aerolinea_db.ingresos_vuelos_por_mes
WHERE mes = '2026-07'
LIMIT 5;
```

**Parámetros:** `mes` (partición); `LIMIT 5`; orden `ingreso_total DESC`
(clustering key). Resultado (fragmento real):

| mes | ingreso_total | vuelo_id |
|---|---|---|
| 2026-07 | 52664.67 | 995 |
| 2026-07 | 48898.71 | 80 |
| 2026-07 | 48466.92 | 622 |

---

## 5. Guía de resolución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Unable to connect to any servers` | Nodos no levantados | `docker compose up -d`; esperar 45 s |
| `UnavailableException (ALL)` | Consistency Level demande réplicas inexistentes | Usar `QUORUM` (recomendado) o `ONE` |
| Consulta lenta | `ALLOW FILTERING` o clave incorrecta | Verificar que el `WHERE` sea partition key |
| No se ven datos | Keyspace/tabla equivocados | Verificar `DESCRIBE KEYSPACE aerolinea_db` |
| `NoHostAvailable` | Driver apuntando a puerto errado | Usar contact points 9042/9142/9242 |

---

## 6. Mantenimiento y apagado del clúster

Los datos persisten en los volúmenes de Docker; `docker compose stop`
(apagado) **no borra datos**. Para apagar todo:

```sh
docker compose down    # detiene y elimina contenedores (más volúmenes intactos)
docker compose down -v # OJO: BORRA los datos (no recomendado)
```

Para reanudar basta `docker compose up -d`; el clúster se reincorpora
automáticamente (nodetool status → 3× UN).
