-- Disponibilidad de asientos desglosada por clase de un vuelo
SELECT vuelo_id, clase, disponibles, ocupados, bloqueados
FROM aerolinea_db.conteo_asientos_por_vuelo_clase
WHERE vuelo_id = 442;

-- Historial cronológico de un pasajero (rango de fechas)
SELECT pasajero_id, fecha_reserva, reserva_id, codigo_vuelo, origen,
       destino, clase, estado_reserva, estado_pago, monto
FROM aerolinea_db.historial_pasajero
WHERE pasajero_id = 4120
  AND fecha_reserva >= '2025-01-01 00:00:00'
  AND fecha_reserva <= '2026-12-31 23:59:59';

-- Manifiesto del vuelo ordenado por asiento
SELECT vuelo_id, asiento, pasajero_nombre, documento, clase,
       estado_reserva, estado_pago
FROM aerolinea_db.manifiesto_vuelo;

-- Ocupación (%) por ruta y rango de meses
SELECT ruta, mes, vuelo_id, reservas_confirmadas, capacidad
FROM aerolinea_db.ocupacion_por_ruta_mes
WHERE ruta = 'GUA-PTY'
  AND mes >= '2026-01'
  AND mes <= '2026-06';

-- Top-5 de vuelos por ingresos del mes
SELECT mes, ingreso_total, vuelo_id, codigo_vuelo
FROM aerolinea_db.ingresos_vuelos_por_mes
WHERE mes = '2026-07'
LIMIT 5;

-- Verificación rápida de que las tablas existen (opcional)
SELECT table_name FROM system_schema.tables
WHERE keyspace_name = 'aerolinea_db';
