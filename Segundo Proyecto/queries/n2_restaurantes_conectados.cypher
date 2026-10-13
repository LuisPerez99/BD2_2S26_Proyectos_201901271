// N2 - Restaurantes altamente conectados: mas chefs trabajando y mas platillos
// destacados (conectividad = num_chefs + num_platillos).

MATCH (r:Restaurante)
OPTIONAL MATCH (r)<-[:TRABAJA_EN]-(c:Chef)
OPTIONAL MATCH (r)-[:OFRECE]->(p:Platillo)
WITH r, count(DISTINCT c) AS num_chefs, count(DISTINCT p) AS num_platillos
RETURN r.nombre AS restaurante, num_chefs, num_platillos,
       (num_chefs + num_platillos) AS conectividad
ORDER BY conectividad DESC, r.nombre
LIMIT 20;