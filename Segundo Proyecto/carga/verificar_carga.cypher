// verificar_carga.cypher - Consultas de validacion de la carga masiva

// 1. Conteo de nodos por etiqueta
MATCH (n)
RETURN labels(n)[0] AS etiqueta, count(*) AS total
ORDER BY etiqueta;

// 2. Conteo de relaciones por tipo
MATCH ()-[r]->()
RETURN type(r) AS tipo, count(r) AS total
ORDER BY tipo;

// 3. Totales globales
MATCH (n) WITH count(n) AS nodos
MATCH ()-[r]->() RETURN nodos, count(r) AS relaciones;

// 4. Propiedades obligatorias nulas por entidad (esperado: nulos = 0)
MATCH (u:Usuario)
RETURN 'Usuario' AS entidad, count(u) AS total,
       sum(CASE WHEN u.nombre IS NULL OR u.email IS NULL OR u.edad IS NULL OR u.pais IS NULL THEN 1 ELSE 0 END) AS nulos;
MATCH (r:Restaurante)
RETURN 'Restaurante' AS entidad, count(r) AS total,
       sum(CASE WHEN r.nombre IS NULL OR r.año_apertura IS NULL OR r.rango_precios IS NULL THEN 1 ELSE 0 END) AS nulos;
MATCH (c:Chef)
RETURN 'Chef' AS entidad, count(c) AS total,
       sum(CASE WHEN c.nombre IS NULL OR c.fecha_nacimiento IS NULL OR c.nacionalidad IS NULL THEN 1 ELSE 0 END) AS nulos;
MATCH (p:Platillo)
RETURN 'Platillo' AS entidad, count(p) AS total,
       sum(CASE WHEN p.nombre IS NULL OR p.precio IS NULL THEN 1 ELSE 0 END) AS nulos;
MATCH (t:TipoCocina)
RETURN 'TipoCocina' AS entidad, count(t) AS total,
       sum(CASE WHEN t.nombre IS NULL THEN 1 ELSE 0 END) AS nulos;

// 5. Validacion de dominio (RN4 y enum de precios; esperado: fuera = 0)
MATCH (:Usuario)-[c:CALIFICÓ]->(:Restaurante)
RETURN 'puntuacion [1,5]' AS chequeo, count(c) AS total,
       sum(CASE WHEN c.puntuacion < 1 OR c.puntuacion > 5 THEN 1 ELSE 0 END) AS fuera_rango;
MATCH (:Usuario)-[g:LE_GUSTA]->(:TipoCocina)
RETURN 'nivel_interes [1,5]' AS chequeo, count(g) AS total,
       sum(CASE WHEN g.nivel_interes < 1 OR g.nivel_interes > 5 THEN 1 ELSE 0 END) AS fuera_rango;
MATCH (r:Restaurante)
RETURN 'rango_precios valido' AS chequeo, count(r) AS total,
       sum(CASE WHEN NOT r.rango_precios IN ['Económico', 'Moderado', 'Caro', 'Premium'] THEN 1 ELSE 0 END) AS invalidos;

// 6. Integridad referencial / cobertura
MATCH (r:Restaurante)
RETURN 'cobertura restaurantes' AS chequeo, count(r) AS total,
       sum(CASE WHEN NOT EXISTS { MATCH (r)<-[:TRABAJA_EN]-() } THEN 1 ELSE 0 END) AS sin_chef,
       sum(CASE WHEN NOT EXISTS { MATCH (r)-[:OFRECE]->() } THEN 1 ELSE 0 END) AS sin_platillo,
       sum(CASE WHEN NOT EXISTS { MATCH (r)-[:PERTENECE_A]->() } THEN 1 ELSE 0 END) AS sin_cocina;
MATCH (u:Usuario)
RETURN 'cobertura usuarios' AS chequeo, count(u) AS total,
       sum(CASE WHEN NOT EXISTS { MATCH (u)-[:ES_AMIGO_DE]-() } THEN 1 ELSE 0 END) AS sin_amistad,
       sum(CASE WHEN NOT EXISTS { MATCH (u)-[:LE_GUSTA]->() } THEN 1 ELSE 0 END) AS sin_preferencia,
       sum(CASE WHEN NOT EXISTS { MATCH (u)-[:VISITÓ]->() } THEN 1 ELSE 0 END) AS sin_visita;

// 7. RN5: mismo platillo ofrecido mas de una vez por restaurante (esperado: 0)
MATCH (r:Restaurante)-[:OFRECE]->(p:Platillo)
WITH r, p, count(*) AS veces
RETURN 'pares restaurante-platillo' AS chequeo, count(*) AS pares,
       sum(CASE WHEN veces > 1 THEN 1 ELSE 0 END) AS duplicados;

// 8. ES_AMIGO_DE no reciproca (esperado: 0)
MATCH (a:Usuario)-[:ES_AMIGO_DE]->(b:Usuario)
RETURN 'amistades no reciprocas' AS chequeo, count(*) AS aristas,
       sum(CASE WHEN NOT EXISTS { MATCH (b)-[:ES_AMIGO_DE]->(a) } THEN 1 ELSE 0 END) AS no_reciprocas;

// 9. Indicadores globales (contexto para Q1-Q5)
MATCH (:Usuario)-[c:CALIFICÓ]->(:Restaurante)
WITH avg(c.puntuacion) AS rating_prom
MATCH (:Usuario)-[v:VISITÓ]->(:Restaurante)
RETURN round(rating_prom, 2) AS rating_global,
       round(avg(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END), 3) AS tasa_reserva_global,
       round(avg(v.consumo), 2) AS consumo_global;
