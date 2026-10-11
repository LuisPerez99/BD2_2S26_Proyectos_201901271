// 00_reset.cypher - Vaciar la base de datos (solo desarrollo)

// Elimina todos los nodos y relaciones en lotes
MATCH (n)
CALL { WITH n DETACH DELETE n }
IN TRANSACTIONS OF 10000 ROWS;

// Borrado manual de constraints e indices (opcional, descomentar)
// DROP CONSTRAINT uniq_usuario_id       IF EXISTS;
// DROP CONSTRAINT uniq_restaurante_id   IF EXISTS;
// DROP CONSTRAINT uniq_chef_id          IF EXISTS;
// DROP CONSTRAINT uniq_platillo_id      IF EXISTS;
// DROP CONSTRAINT uniq_tipococina_id    IF EXISTS;
// DROP CONSTRAINT uniq_usuario_email    IF EXISTS;
// DROP CONSTRAINT uniq_tipococina_nombre IF EXISTS;
// DROP INDEX idx_restaurante_nombre IF EXISTS;
// DROP INDEX idx_restaurante_rango  IF EXISTS;
// DROP INDEX idx_chef_nacionalidad  IF EXISTS;
