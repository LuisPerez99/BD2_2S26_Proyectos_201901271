-- =====================================================================
-- 02_schema.cql
-- Esquema lógico basado en QUERIES (Query-Driven Modeling).
--
-- Principio: en Cassandra NO existen JOINs ni se debe usar
-- ALLOW FILTERING. Por lo tanto se crea UNA TABLA POR PATRÓN DE
-- ACCESO, con datos denormalizados y claves (partition + clustering)
-- elegidas para resolver cada consulta con UNA sola búsqueda por
-- partición y ordenamiento nativo por clustering key.
--
-- TABLAS BASE (fuentes de verdad) y TABLAS ESPECIALIZADAS (1 por query):
--   Base:  aeronaves, pasajeros, vuelos, asientos_por_vuelo, reservas,
--          pagos_por_reserva
--   Q1:    conteo_asientos_por_vuelo_clase        (contadores)
--   Q2:    historial_pasajero                     (reserva + pago)
--   Q3:    manifiesto_vuelo                       (3 entidades)
--   Q4:    ocupacion_por_ruta_mes                 (contadores + bucket)
--   Q5:    ingresos_vuelos_por_mes                (agregación DESC)
-- =====================================================================

-- ---------------------------------------------------------------------
-- TABLAS BASE
-- ---------------------------------------------------------------------

-- Aeronaves: fuente de verdad del parque aéreo.
CREATE TABLE IF NOT EXISTS aerolinea_db.aeronaves (
    aeronave_id     int PRIMARY KEY,
    modelo          text,
    aerolinea       text,
    matricula       text,
    capacidad_max   int
);

-- Pasajeros: fuente de verdad del directorio de pasajeros.
CREATE TABLE IF NOT EXISTS aerolinea_db.pasajeros (
    pasajero_id     int PRIMARY KEY,
    nombre          text,
    email           text,
    documento       text,          -- pasaporte o DPI
    telefono        text,
    nacionalidad    text
);

-- Vuelos: fuente de verdad de trayectos programados.
-- Se denormaliza `ruta` ("origen-destino"), `capacidad` y el modelo de
-- la aeronave para alimentar las tablas de agregación sin JOIN.
CREATE TABLE IF NOT EXISTS aerolinea_db.vuelos (
    vuelo_id        int PRIMARY KEY,
    codigo          text,
    aeronave_id     int,
    aeronave_modelo text,
    capacidad       int,
    origen          text,
    destino         text,
    ruta            text,          -- "origen-destino"
    fecha_salida    timestamp,
    fecha_llegada   timestamp,
    estado          text           -- programado | retrasado | cancelado | completado
);

-- Asientos por vuelo: unidad de capacidad de cada vuelo.
-- Partition key = vuelo_id, clustering = asiento (orden natural).
CREATE TABLE IF NOT EXISTS aerolinea_db.asientos_por_vuelo (
    vuelo_id    int,
    asiento     text,          -- "001A" (padding para que el orden alfabético == numérico)
    clase       text,          -- economica | ejecutiva | primera
    estado      text,          -- disponible | ocupado | bloqueado
    PRIMARY KEY (vuelo_id, asiento)
);

-- Reservas: fuente de verdad de cada reserva.
CREATE TABLE IF NOT EXISTS aerolinea_db.reservas (
    reserva_id      int PRIMARY KEY,
    pasajero_id     int,
    vuelo_id        int,
    asiento         text,
    fecha_reserva   timestamp,
    estado          text           -- pendiente | confirmada | cancelada
);

-- Pagos por reserva: fuente de verdad de cada transacción.
CREATE TABLE IF NOT EXISTS aerolinea_db.pagos_por_reserva (
    reserva_id      int PRIMARY KEY,
    monto           decimal,
    metodo_pago     text,          -- tarjeta | transferencia | efectivo
    fecha_pago      timestamp,
    estado_pago     text           -- pendiente | pagado | reembolsado
);

-- ---------------------------------------------------------------------
-- TABLA ESPECIALIZADA Q1
-- Disponibilidad de asientos por clase para un vuelo.
--   SELECT clase, disponibles, ocupados, bloqueados
--   FROM conteo_asientos_por_vuelo_clase WHERE vuelo_id = ?;
--
-- Partition key (vuelo_id) + clustering (clase): 1 fila por clase del
-- vuelo. COUNT en tiempo de lectura NO es permitido en Cassandra, por
-- eso se usa una tabla de CONTADORES que se incrementa/decrementa en
-- cada reserva/cancelación/baja de asiento. La agregación vive en la BD.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.conteo_asientos_por_vuelo_clase (
    vuelo_id     int,
    clase        text,
    disponibles  counter,
    ocupados     counter,
    bloqueados   counter,
    PRIMARY KEY (vuelo_id, clase)
);

-- ---------------------------------------------------------------------
-- TABLA ESPECIALIZADA Q2
-- Historial cronológico de un pasajero en un rango de fechas.
--   SELECT * FROM historial_pasajero
--   WHERE pasajero_id = ? AND fecha_reserva >= ? AND fecha_reserva <= ?
--   ORDER BY fecha_reserva ASC;
--
-- Partition key = pasajero_id (todo el historial de un pasajero es 1
-- partición). Clustering key = (fecha_reserva, reserva_id) para:
--   * orden cronológico nativo (comparadores >= / <= resueltos por la
--     clave de clustering, sin ALLOW FILTERING),
--   * unicidad si dos reservas comparten fecha.
-- Se denormaliza la información del vuelo y del PAGO de cada reserva:
-- ambas consultas (detalle de reserva + estado de pago) se responden
-- con una sola lectura.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.historial_pasajero (
    pasajero_id      int,
    fecha_reserva    timestamp,
    reserva_id       int,
    vuelo_id         int,
    codigo_vuelo     text,
    origen           text,
    destino          text,
    fecha_salida     timestamp,
    asiento          text,
    clase            text,
    estado_reserva   text,          -- pendiente | confirmada | cancelada
    estado_pago      text,          -- pendiente | pagado | reembolsado
    monto            decimal,
    metodo_pago      text,
    fecha_pago       timestamp,
    PRIMARY KEY (pasajero_id, fecha_reserva, reserva_id)
) WITH CLUSTERING ORDER BY (fecha_reserva DESC, reserva_id DESC);

-- ---------------------------------------------------------------------
-- TABLA ESPECIALIZADA Q3
-- Manifiesto de vuelo ordenado por número de asiento y enriquecido.
--   SELECT * FROM manifiesto_vuelo WHERE vuelo_id = ?;
--
-- Partition key = vuelo_id (el manifiesto cabe cómodo en 1 partición:
-- ~180 asientos). Clustering = asiento con padding "001A" para que el
-- orden físico nativo del clustering = orden por número de asiento.
-- Denormaliza tres entidades: PASAJERO (nombre, documento,
-- nacionalidad) + la RESERVA (clase, estado) + el PAGO (estado):
-- el manifiesto enriquecido es UNA sola consulta, sin JOIN.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.manifiesto_vuelo (
    vuelo_id        int,
    asiento         text,          -- padding numérico, ej. "005C"
    pasajero_id     int,
    pasajero_nombre text,
    documento       text,
    nacionalidad    text,
    clase           text,
    estado_reserva  text,
    estado_pago     text,
    PRIMARY KEY (vuelo_id, asiento)
) WITH CLUSTERING ORDER BY (asiento ASC);

-- ---------------------------------------------------------------------
-- TABLA ESPECIALIZADA Q4
-- Porcentaje de ocupación por ruta y rango de fechas.
--   SELECT vuelo_id, reservas_confirmadas, capacidad
--   FROM ocupacion_por_ruta_mes
--   WHERE ruta = ? AND mes >= ? AND mes <= ?;
--
-- BUCKETING: la partición es por RUTA y el clustering por (mes, vuelo)
-- evita particiones gigantes (un mes de una ruta tiene ~10 vuelos).
-- Es una tabla de CONTADORES:
--   * reservas_confirmadas: se incrementa al confirmar, decrementa al
--     cancelar.
--   * capacidad: se "fija" como contador usando UPDATE ... = capacidad
--     + suma inicial (los contadores no admiten columnas normales).
-- El % se obtiene como reservas_confirmadas / capacidad en el cliente
-- con dos contadores de una SOLA fila (agregación en la BD, no en el
-- cliente). `mes` usa formato "YYYY-MM" (ISO) para comparadores de
-- rango lexicográficos válidos.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.ocupacion_por_ruta_mes (
    ruta                 text,     -- "origen-destino"
    mes                  text,     -- "YYYY-MM"
    vuelo_id             int,
    reservas_confirmadas counter,
    capacidad            counter,
    PRIMARY KEY (ruta, mes, vuelo_id)
);

-- ---------------------------------------------------------------------
-- TABLA ESPECIALIZADA Q5
-- Top N de vuelos por ingresos dentro de un rango de fechas.
--   SELECT * FROM ingresos_vuelos_por_mes WHERE mes = ? LIMIT 3;
--
-- Tabla de AGREGACIÓN: partition por bucket de mes, clustering key =
-- (ingreso_total DESC, vuelo_id). Como la clave de clustering lleva el
-- MONTO en orden DESCENDENTE, el `LIMIT N` devuelve el Top N SIN ordenar
-- ni filtrar en el cliente.
--
-- Patrón de actualización: el monto forma parte de la PK, así que una
-- variación de ingreso se aplica como DELETE (mes, monto_viejo, vuelo)
-- + INSERT (mes, monto_nuevo, vuelo). En la carga masiva basta insertar
-- los totales finales por (mes, vuelo) porque se calculan previamente.
-- Para un rango de varios meses se consulta el bucket de cada mes y se
-- fusionan los tops (patrón equivalente documentado en la doc técnica).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.ingresos_vuelos_por_mes (
    mes            text,          -- "YYYY-MM" (bucket)
    ingreso_total  decimal,       -- suma de pagos pagados del vuelo en el mes
    vuelo_id       int,
    codigo_vuelo   text,
    PRIMARY KEY (mes, ingreso_total, vuelo_id)
) WITH CLUSTERING ORDER BY (ingreso_total DESC, vuelo_id ASC);

-- ---------------------------------------------------------------------
-- TABLA CON TTL — reservas expiradas (eliminación automática)
-- Alcance obligatorio: "Configurar TTL (Time-To-Live) para eliminar
-- reservas expiradas automáticamente".
--
-- Contiene las reservas que pierden vigencia (canceladas o pendientes
-- sin pago). Se insertan con TTL de 90 días (7,776,000 s) configurado
-- en `default_time_to_live`: Cassandra las elimina SOLAS al expirar, sin
-- intervención ni job de limpieza. El TTL puede consultarse en vivo con
-- `SELECT TTL(estado) ...` (segundos restantes).
--
-- Las reservas *confirmadas y pagadas* (historial/auditoría) viven
-- intactas en `reservas` e `historial_pasajero`: solo se expiran las que
-- dejan de ser válidas.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aerolinea_db.reservas_expiradas (
    reserva_id     int PRIMARY KEY,
    pasajero_id    int,
    vuelo_id       int,
    asiento        text,
    fecha_reserva  timestamp,
    estado         text           -- cancelada | pendiente
) WITH default_time_to_live = 7776000;   -- 90 días en segundos