// 01_load_nodes.cypher - Carga masiva de nodos con LOAD CSV + MERGE

// Usuarios
LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
CALL (row) {
  MERGE (u:Usuario {usuario_id: toInteger(row.usuario_id)})
  SET u.nombre = row.nombre,
      u.email  = row.email,
      u.edad   = toInteger(row.edad),
      u.pais   = row.pais
} IN TRANSACTIONS OF 1000 ROWS;

// Restaurantes
LOAD CSV WITH HEADERS FROM 'file:///restaurantes.csv' AS row
CALL (row) {
  MERGE (r:Restaurante {restaurante_id: toInteger(row.restaurante_id)})
  SET r.nombre        = row.nombre,
      r.año_apertura = toInteger(row.año_apertura),
      r.rango_precios = row.rango_precios,
      r.descripcion   = row.descripcion
} IN TRANSACTIONS OF 1000 ROWS;

// Chefs
LOAD CSV WITH HEADERS FROM 'file:///chefs.csv' AS row
CALL (row) {
  MERGE (c:Chef {chef_id: toInteger(row.chef_id)})
  SET c.nombre           = row.nombre,
      c.fecha_nacimiento = date(row.fecha_nacimiento),
      c.nacionalidad     = row.nacionalidad
} IN TRANSACTIONS OF 1000 ROWS;

// Platillos
LOAD CSV WITH HEADERS FROM 'file:///platillos.csv' AS row
CALL (row) {
  MERGE (p:Platillo {platillo_id: toInteger(row.platillo_id)})
  SET p.nombre      = row.nombre,
      p.precio      = toFloat(row.precio),
      p.descripcion = row.descripcion
} IN TRANSACTIONS OF 1000 ROWS;

// Tipos de cocina
LOAD CSV WITH HEADERS FROM 'file:///tipos_cocina.csv' AS row
CALL (row) {
  MERGE (t:TipoCocina {tipo_cocina_id: toInteger(row.tipo_cocina_id)})
  SET t.nombre      = row.nombre,
      t.descripcion = row.descripcion
} IN TRANSACTIONS OF 1000 ROWS;
