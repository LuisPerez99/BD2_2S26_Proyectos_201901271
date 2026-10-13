// N1 - Ruta mas corta entre dos usuarios (grados de separacion) con
// shortestPath sobre ES_AMIGO_DE.
// Parametros: $a, $b (emails de los usuarios).

MATCH (a:Usuario {email: $a}), (b:Usuario {email: $b}),
      p = shortestPath((a)-[:ES_AMIGO_DE*..20]-(b))
RETURN a.nombre AS desde, b.nombre AS hasta,
       length(p) AS grados_de_separacion,
       [n IN nodes(p) | n.nombre] AS camino;