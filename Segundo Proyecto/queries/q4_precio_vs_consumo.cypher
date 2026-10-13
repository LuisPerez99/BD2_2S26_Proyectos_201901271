// Q4 - Comparacion del rango de precios declarado contra el consumo promedio
// real registrado en las visitas; mayor diferencia primero.

MATCH (r:Restaurante)<-[v:VISITÓ]-(:Usuario)
WITH r, avg(v.consumo) AS consumo_real
WITH r, consumo_real,
     CASE r.rango_precios
       WHEN 'Económico' THEN 100.0
       WHEN 'Moderado'  THEN 250.0
       WHEN 'Caro'      THEN 500.0
       WHEN 'Premium'   THEN 900.0
       ELSE 0.0 END AS consumo_esperado
RETURN r.nombre AS restaurante, r.rango_precios AS rango,
       round(consumo_real, 2) AS consumo_real,
       consumo_esperado,
       round(consumo_real - consumo_esperado, 2) AS diferencia
ORDER BY diferencia DESC
LIMIT 20;