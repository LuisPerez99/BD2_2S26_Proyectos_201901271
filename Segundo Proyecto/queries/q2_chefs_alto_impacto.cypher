// Q2 - Chefs de alto impacto: trabajan en restaurantes con calificacion
// promedio superior a 4 estrellas y sus platillos se ofrecen en al menos
// 3 restaurantes distintos.

MATCH (chef:Chef)-[:TRABAJA_EN]->(r:Restaurante)<-[c:CALIFICÓ]-(:Usuario)
WITH chef, r, avg(c.puntuacion) AS prom_r
WITH chef, avg(prom_r) AS prom_restaurantes
WHERE prom_restaurantes > 4
MATCH (chef)-[:PREPARA]->(:Platillo)<-[:OFRECE]-(otro:Restaurante)
WITH chef, prom_restaurantes, count(DISTINCT otro) AS restaurantes_platillos
WHERE restaurantes_platillos >= 3
RETURN chef.nombre AS chef,
       round(prom_restaurantes, 2) AS prom_restaurantes,
       restaurantes_platillos
ORDER BY restaurantes_platillos DESC, prom_restaurantes DESC
LIMIT 20;