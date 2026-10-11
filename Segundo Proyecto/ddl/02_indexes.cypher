// 02_indexes.cypher - Indices secundarios (Neo4j 5.x Community)

// Restaurante: nombre, rango de precios y anio de apertura
CREATE INDEX idx_restaurante_nombre IF NOT EXISTS
FOR (r:Restaurante) ON (r.nombre);

CREATE INDEX idx_restaurante_rango IF NOT EXISTS
FOR (r:Restaurante) ON (r.rango_precios);

CREATE INDEX idx_restaurante_anio IF NOT EXISTS
FOR (r:Restaurante) ON (r.anio_apertura);

// Chef: nacionalidad (usado en Q2)
CREATE INDEX idx_chef_nacionalidad IF NOT EXISTS
FOR (c:Chef) ON (c.nacionalidad);

// Usuario: pais
CREATE INDEX idx_usuario_pais IF NOT EXISTS
FOR (u:Usuario) ON (u.pais);

// Platillo: precio
CREATE INDEX idx_platillo_precio IF NOT EXISTS
FOR (p:Platillo) ON (p.precio);

// Relaciones: puntuacion, fecha, reserva y puesto
CREATE INDEX idx_califico_puntuacion IF NOT EXISTS
FOR ()-[c:CALIFICÓ]-() ON (c.puntuacion);

CREATE INDEX idx_visito_fecha IF NOT EXISTS
FOR ()-[v:VISITÓ]-() ON (v.fecha);

CREATE INDEX idx_visito_reserva IF NOT EXISTS
FOR ()-[v:VISITÓ]-() ON (v.con_reserva);

CREATE INDEX idx_trabajaen_puesto IF NOT EXISTS
FOR ()-[t:TRABAJA_EN]-() ON (t.puesto);

// Verificacion: listar los indices creados
// SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state
// RETURN name, type, labelsOrTypes, properties, state;
