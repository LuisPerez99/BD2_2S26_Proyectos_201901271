// 02_load_rels.cypher - Carga masiva de relaciones con LOAD CSV + MERGE

// CALIFICÓ: Usuario -> Restaurante
LOAD CSV WITH HEADERS FROM 'file:///califico.csv' AS row
CALL (row) {
  MATCH (u:Usuario {usuario_id: toInteger(row.usuario_id)})
  MATCH (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  MERGE (u)-[c:CALIFICÓ]->(r)
  SET c.puntuacion = toInteger(row.puntuacion),
      c.fecha      = date(row.fecha),
      c.comentario = CASE WHEN row.comentario = '' THEN null ELSE row.comentario END
} IN TRANSACTIONS OF 1000 ROWS;

// VISITÓ: Usuario -> Restaurante
LOAD CSV WITH HEADERS FROM 'file:///visito.csv' AS row
CALL (row) {
  MATCH (u:Usuario {usuario_id: toInteger(row.usuario_id)})
  MATCH (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  MERGE (u)-[v:VISITÓ]->(r)
  SET v.fecha       = date(row.fecha),
      v.consumo     = toFloat(row.consumo),
      v.con_reserva = toBoolean(row.con_reserva)
} IN TRANSACTIONS OF 1000 ROWS;

// ES_AMIGO_DE: Usuario -> Usuario
LOAD CSV WITH HEADERS FROM 'file:///es_amigo_de.csv' AS row
CALL (row) {
  MATCH (u:Usuario {usuario_id: toInteger(row.usuario_id)})
  MATCH (a:Usuario {usuario_id: toInteger(row.amigo_id)})
  MERGE (u)-[e:ES_AMIGO_DE]->(a)
  SET e.fecha_amistad = date(row.fecha_amistad)
} IN TRANSACTIONS OF 1000 ROWS;

// PERTENECE_A: Restaurante -> TipoCocina
LOAD CSV WITH HEADERS FROM 'file:///pertenece_a.csv' AS row
CALL (row) {
  MATCH (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  MATCH (t:TipoCocina {tipo_cocina_id: toInteger(row.tipo_cocina_id)})
  MERGE (r)-[:PERTENECE_A]->(t)
} IN TRANSACTIONS OF 1000 ROWS;

// OFRECE: Restaurante -> Platillo
LOAD CSV WITH HEADERS FROM 'file:///ofrece.csv' AS row
CALL (row) {
  MATCH (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
  MERGE (r)-[o:OFRECE]->(p)
  SET o.precio      = toFloat(row.precio),
      o.disponible  = toBoolean(row.disponible)
} IN TRANSACTIONS OF 1000 ROWS;

// PREPARA: Chef -> Platillo
LOAD CSV WITH HEADERS FROM 'file:///prepara.csv' AS row
CALL (row) {
  MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
  MATCH (p:Platillo {platillo_id: toInteger(row.platillo_id)})
  MERGE (c)-[pr:PREPARA]->(p)
  SET pr.estilo       = row.estilo,
      pr.especialidad = toBoolean(row.especialidad)
} IN TRANSACTIONS OF 1000 ROWS;

// TRABAJA_EN: Chef -> Restaurante
LOAD CSV WITH HEADERS FROM 'file:///trabaja_en.csv' AS row
CALL (row) {
  MATCH (c:Chef {chef_id: toInteger(row.chef_id)})
  MATCH (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  MERGE (c)-[t:TRABAJA_EN]->(r)
  SET t.fecha_inicio = date(row.fecha_inicio),
      t.puesto       = row.puesto
} IN TRANSACTIONS OF 1000 ROWS;

// LE_GUSTA: Usuario -> TipoCocina
LOAD CSV WITH HEADERS FROM 'file:///le_gusta.csv' AS row
CALL (row) {
  MATCH (u:Usuario {usuario_id: toInteger(row.usuario_id)})
  MATCH (t:TipoCocina {tipo_cocina_id: toInteger(row.tipo_cocina_id)})
  MERGE (u)-[g:LE_GUSTA]->(t)
  SET g.nivel_interes = toInteger(row.nivel_interes)
} IN TRANSACTIONS OF 1000 ROWS;
