// Q5 - Discrepancia entre la cocina favorita declarada (LE_GUSTA con mayor
// nivel de interes) y la cocina realmente visitada con mayor frecuencia
// (VISITÓ -> PERTENECE_A).

MATCH (u:Usuario)-[g:LE_GUSTA]->(td:TipoCocina)
WITH u, td, g.nivel_interes AS nivel
ORDER BY nivel DESC, td.tipo_cocina_id ASC
WITH u, collect(td)[0] AS cocina_declarada, collect(nivel)[0] AS nivel_declarado
MATCH (u)-[:VISITÓ]->(r:Restaurante)-[:PERTENECE_A]->(tv:TipoCocina)
WITH u, cocina_declarada, nivel_declarado, tv, count(*) AS visitas
ORDER BY visitas DESC, tv.tipo_cocina_id ASC
WITH u, cocina_declarada, nivel_declarado,
     collect(tv)[0] AS cocina_real, collect(visitas)[0] AS visitas_cocina
RETURN u.nombre AS usuario,
       cocina_declarada.nombre AS cocina_declarada, nivel_declarado,
       cocina_real.nombre AS cocina_real, visitas_cocina,
       CASE WHEN cocina_declarada = cocina_real THEN false ELSE true END AS discrepancia
ORDER BY discrepancia DESC, visitas_cocina DESC
LIMIT 20;