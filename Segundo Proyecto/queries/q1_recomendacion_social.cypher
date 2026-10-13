// Q1 - Recomendacion social: restaurantes con calificacion >= 4
// dados por amigos (directos e indirectos, hasta 3 grados de separacion),
// excluyendo los ya visitados, ordenados por amigos coincidentes y rating.
// Parametro: $email del usuario objetivo.

MATCH (u:Usuario {email: $email})-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
MATCH (amigo)-[c:CALIFICÓ]->(r:Restaurante)
WHERE c.puntuacion >= 4
  AND NOT (u)-[:VISITÓ]->(r)
WITH r, count(DISTINCT amigo) AS amigos_coincidentes, avg(c.puntuacion) AS calificacion_prom
RETURN r.nombre AS restaurante,
       amigos_coincidentes,
       round(calificacion_prom, 2) AS calificacion_prom
ORDER BY amigos_coincidentes DESC, calificacion_prom DESC, r.nombre
LIMIT 20;