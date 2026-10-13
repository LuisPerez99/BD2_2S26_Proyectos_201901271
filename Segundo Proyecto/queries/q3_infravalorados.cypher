// Q3 - Restaurantes infravalorados: tasa de visitas con reserva superior a la
// media general de la plataforma y calificacion promedio inferior a la media.

MATCH (:Usuario)-[v:VISITÓ]->(:Restaurante)
WITH sum(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) / count(v) AS g_reserva
MATCH (:Usuario)-[c:CALIFICÓ]->(:Restaurante)
WITH g_reserva, avg(c.puntuacion) AS g_rating
MATCH (r:Restaurante)<-[v2:VISITÓ]-(:Usuario)
WITH r, g_reserva, g_rating,
     avg(CASE WHEN v2.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva
MATCH (r)<-[c2:CALIFICÓ]-(:Usuario)
WITH r, g_reserva, g_rating, tasa_reserva,
     avg(c2.puntuacion) AS prom_rating
WHERE tasa_reserva > g_reserva AND prom_rating < g_rating
RETURN r.nombre AS restaurante, r.rango_precios AS rango,
       round(tasa_reserva, 3) AS tasa_reserva,
       round(prom_rating, 2) AS prom_rating,
       round(g_reserva, 3) AS tasa_global,
       round(g_rating, 2) AS rating_global
ORDER BY (tasa_reserva - g_reserva) DESC
LIMIT 20;