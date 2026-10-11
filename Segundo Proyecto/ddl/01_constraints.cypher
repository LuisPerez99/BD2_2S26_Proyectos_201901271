// 01_constraints.cypher - Constraints del modelo (Neo4j 5.x Community)

// Unicidad de identificadores logicos (claves de negocio para MERGE)
CREATE CONSTRAINT uniq_usuario_id IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.usuario_id IS UNIQUE;

CREATE CONSTRAINT uniq_restaurante_id IF NOT EXISTS
FOR (r:Restaurante) REQUIRE r.restaurante_id IS UNIQUE;

CREATE CONSTRAINT uniq_chef_id IF NOT EXISTS
FOR (c:Chef) REQUIRE c.chef_id IS UNIQUE;

CREATE CONSTRAINT uniq_platillo_id IF NOT EXISTS
FOR (p:Platillo) REQUIRE p.platillo_id IS UNIQUE;

CREATE CONSTRAINT uniq_tipococina_id IF NOT EXISTS
FOR (t:TipoCocina) REQUIRE t.tipo_cocina_id IS UNIQUE;

// Unicidad de claves naturales
CREATE CONSTRAINT uniq_usuario_email IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.email IS UNIQUE;

CREATE CONSTRAINT uniq_tipococina_nombre IF NOT EXISTS
FOR (t:TipoCocina) REQUIRE t.nombre IS UNIQUE;

// Verificacion: listar los constraints creados
// SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
// RETURN name, type, labelsOrTypes, properties;

// Existencia de propiedades: solo Neo4j Enterprise (no descomentar en Community)
// CREATE CONSTRAINT ex_usuario_email IF NOT EXISTS
// FOR (u:Usuario) REQUIRE u.email IS NOT NULL;
// CREATE CONSTRAINT ex_restaurante_rango IF NOT EXISTS
// FOR (r:Restaurante) REQUIRE r.rango_precios IS NOT NULL;
// CREATE CONSTRAINT ex_chef_nacionalidad IF NOT EXISTS
// FOR (c:Chef) REQUIRE c.nacionalidad IS NOT NULL;

// RN4: puntuacion en [1,5] se valida en generacion y en las consultas
// RN5: unicidad (Restaurante)-[:OFRECE]->(Platillo) se hace con MERGE en carga
