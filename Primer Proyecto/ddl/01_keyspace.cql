-- =====================================================================
-- 01_keyspace.cql
-- Keyspace del proyecto "Sistema de Reservas y Boletos Aéreos"
--
-- Estrategia de replicación: NetworkTopologyStrategy.
--   * Se elige NTS (y no SimpleStrategy) porque es la estrategia
--     recomendada por DataStax: soporta múltiples datacenters y permite
--     definir un Replication Factor por DC. Aunque este laboratorio usa
--     un solo DC (dc1), al usar NTS la topología es transparente si en
--     el futuro se agregan datacenters.
--   * RF=3 === réplica completa en cada nodo del DC. Esto permite
--     alcanzar Consistencia QUORUM (2 réplicas ack) y ALL (3 réplicas
--     ack), que son los niveles que se evaluarán en las pruebas.
-- =====================================================================

CREATE KEYSPACE IF NOT EXISTS aerolinea_db
WITH replication = {
  'class'              : 'NetworkTopologyStrategy',
  'dc1'                : 3
}
AND durable_writes = true;