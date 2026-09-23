-- =====================================================================
-- consultas/consultas_q1_q5.cql
-- Las 5 consultas de negocio (Fase 5) para aerolinea_db.
--
-- Diseño: cada consulta se resuelve con UNA lectura de partición sobre
-- una tabla especializada (Query-Driven Modeling). No usa JOIN, no usa
-- ALLOW FILTERING y no necesita "ORDER BY" en el cliente: el orden lo
-- da la CLUSTERING KEY.
--
-- Ejecución local:
--   docker exec -i cassandra1 cqlsh -k aerolinea_db -f consultas_q1_q5.cql
-- =====================================================================

-- ---------------------------------------------------------------------
-- Q1 — Disponibilidad de asientos desglosada por clase de un vuelo
-- Tabla: conteo_asientos_por_vuelo_clase (COUNTER)
--   PK(vuelo_id) · CL(clase)
-- ---------------------------------------------------------------------
SELECT vuelo_id, clase, disponibles, ocupados, bloqueados
FROM aerolinea_db.conteo_asientos_por_vuelo_clase
WHERE vuelo_id = 442;

-- ---------------------------------------------------------------------
-- Q2 — Historial cronológico de un pasajero (rango de fechas)
-- Tabla: historial_pasajero
--   PK(pasajero_id) · CL(fecha_reserva DESC, reserva_id DESC)
-- ---------------------------------------------------------------------
SELECT pasajero_id, fecha_reserva, reserva_id, codigo_vuelo, origen,
       destino, clase, estado_reserva, estado_pago, monto
FROM aerolinea_db.historial_pasajero
WHERE pasajero_id = 75
  AND fecha_reserva >= '2025-01-01 00:00:00'
  AND fecha_reserva <= '2025-12-31 23:59:59';

-- ---------------------------------------------------------------------
-- Q3 — Manifiesto del vuelo ordenado por asiento
-- Tabla: manifiesto_vuelo
--   PK(vuelo_id) · CL(asiento)
-- ---------------------------------------------------------------------
SELECT vuelo_id, asiento, pasajero_nombre, documento, clase,
       estado_reserva, estado_pago
FROM aerolinea_db.manifiesto_vuelo
WHERE vuelo_id = 1203;

-- ---------------------------------------------------------------------
-- Q4 — Ocupación (%) por ruta y rango de meses
-- Tabla: ocupacion_por_ruta_mes (COUNTER)
--   PK(ruta) · CL(mes, vuelo_id)
-- ---------------------------------------------------------------------
SELECT ruta, mes, vuelo_id, reservas_confirmadas, capacidad
FROM aerolinea_db.ocupacion_por_ruta_mes
WHERE ruta = 'GUA-PTY'
  AND mes >= '2026-01'
  AND mes <= '2026-06';

-- ---------------------------------------------------------------------
-- Q5 — Top-5 de vuelos por ingresos del mes
-- Tabla: ingresos_vuelos_por_mes (DETALLE)
--   PK(mes) · CL(ingreso_total DESC, vuelo_id)
-- Ocupación: el Top-N se lee ya ordenado por la clustering key; el
-- vuelo de mayor ingreso es la primera fila de la partición.
-- ---------------------------------------------------------------------
SELECT mes, ingreso_total, vuelo_id, codigo_vuelo
FROM aerolinea_db.ingresos_vuelos_por_mes
WHERE mes = '2026-07'
LIMIT 5;

-- =====================================================================
-- Verificación rápida de que las tablas existen (opcional)
-- =====================================================================
SELECT table_name FROM system_schema.tables
WHERE keyspace_name = 'aerolinea_db';
