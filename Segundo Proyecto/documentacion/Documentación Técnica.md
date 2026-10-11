# Análisis de Requerimientos y Modelado Conceptual

> **Proyecto:** Sistema de Recomendación de Restaurantes con Neo4j
> **Fase:** 1 de 6 — Análisis de Requerimientos y Modelado Conceptual
> **Entregable asociado:** Documentación Técnica (modelo conceptual de grafos)
> **Estado:** Diseño conceptual (sin implementación en Neo4j)

---

## 1. Propósito de la fase

En esta fase se analiza el problema de negocio, se identifican las entidades
(nodos), sus atributos (propiedades) y las relaciones (aristas) que las conectan,
y se construye el **modelo conceptual de grafos**. El modelo debe ser lo
suficientemente expresivo como para responder las consultas de recomendación,
análisis de redes y detección de patrones definidas en el enunciado.

El resultado de esta fase es un modelo **independiente del motor**, que en la
Fase 2 se transformará en el esquema implementable en Neo4j.

---

## 2. Análisis de requerimientos del negocio

### 2.1. Descripción del dominio

La plataforma conecta **usuarios** que buscan dónde comer con **restaurantes**
que ofrecen **platillos**, clasificados por **tipos de cocina** y liderados por
**chefs**. El valor del sistema no está en las entidades aisladas, sino en la
**red de relaciones** que se forma entre ellas:

- Usuarios que califican y visitan restaurantes.
- Usuarios que son amigos entre sí (red social).
- Usuarios que declaran preferencia por tipos de cocina.
- Restaurantes que pertenecen a uno o varios tipos de cocina.
- Restaurantes que ofrecen platillos y chefs que trabajan en restaurantes.
- Chefs que preparan platillos.

El negocio desea aprovechar esta red para **recomendar restaurantes** combinando
las preferencias propias del usuario con el comportamiento de su círculo social
(hasta 3 grados de separación).

### 2.2. Objetivos del sistema

| # | Objetivo | Descripción |
| :-: | :--- | :--- |
| O1 | Modelado natural de relaciones | Representar de forma intuitiva las conexiones entre usuarios, restaurantes, chefs, tipos de cocina y platillos. |
| O2 | Consultas eficientes multi-nivel | Recorrer varios niveles de relaciones (amigos de amigos, chefs → restaurantes → platillos) con buen desempeño. |
| O3 | Análisis de redes | Calcular grados de separación entre usuarios (`shortestPath`) e identificar restaurantes altamente conectados. |
| O4 | Recomendaciones inteligentes | Sugerir restaurantes a partir de chefs compartidos, historial de calificaciones y patrones de visita/consumo. |

### 2.3. Reglas de negocio (identificadas del enunciado)

| # | Regla de negocio | Impacto en el modelo |
| :-: | :--- | :--- |
| RN1 | Un usuario puede calificar y visitar múltiples restaurantes. | Cardinalidad N:M entre `Usuario` y `Restaurante` mediante dos relaciones distintas (`CALIFICÓ` y `VISITÓ`). |
| RN2 | Un restaurante puede pertenecer a varios tipos de cocina y ofrecer múltiples platillos. | Relaciones N:M `PERTENECE_A` y `OFRECE`. |
| RN3 | Un chef puede trabajar en varios restaurantes y preparar múltiples platillos. | Relaciones N:M `TRABAJA_EN` y `PREPARA`. |
| RN4 | Las calificaciones deben estar en el rango de 1 a 5 estrellas. | La propiedad `puntuacion` de `CALIFICÓ` debe validarse en `[1,5]`. |
| RN5 | Un restaurante no puede ofrecer el mismo platillo más de una vez. | Unicidad en el par `(Restaurante)-[:OFRECE]->(Platillo)`. |
| RN6 | Recomendar restaurantes según calificaciones altas (≥ 4) de amigos, directos e indirectos, hasta 3 grados de separación, excluyendo restaurantes ya visitados. | Requiere traversal de longitud variable sobre `ES_AMIGO_DE` y filtrado sobre `CALIFICÓ`/`VISITÓ`. |

### 2.4. Supuestos y decisiones de alcance

| # | Supuesto / decisión | Justificación |
| :-: | :--- | :--- |
| S1 | Cada entidad tiene un **identificador lógico** (`*_id`) además de su nombre. | Permite `MERGE` sin duplicados en la carga masiva y claves de negocio estables. |
| S2 | `ES_AMIGO_DE` se modela en **ambos sentidos** para facilitar el traversal. | El enunciado describe amistad recíproca; se documenta como relación dirigida replicada (aunque el traversal puede ignorar la dirección). |
| S3 | `Rango de Precios` se almacena como **categoría discreta** (`Económico`, `Moderado`, `Caro`, `Premium`). | Facilita la consulta de comparación precio declarado vs. consumo real mediante un mapeo categórico → rango esperado. |
| S4 | El consumo real de una visita se almacena en la relación `VISITÓ` (no en el usuario ni en el restaurante). | El consumo depende del par usuario–restaurante–fecha, no de una entidad aislada. |
| S5 | La fecha de amistad se almacena en la relación `ES_AMIGO_DE`. | Propiedad del vínculo, no de los usuarios. |

---

## 3. Identificación de entidades (nodos)

Se identifican **cinco tipos de nodo**. Las etiquetas siguen la convención del
enunciado: **singular y CamelCase**.

### 3.1. `Usuario`

Personas que utilizan la plataforma.

| Propiedad (enunciado) | Nombre técnico | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| Nombre | `nombre` | String | Sí | Nombre completo del usuario. |
| Email | `email` | String | Sí | Correo electrónico; **único** (clave natural). |
| Edad | `edad` | Integer | Sí | Edad en años (≥ 18). |
| País | `pais` | String | Sí | País de residencia. |
| — (técnico) | `usuario_id` | Integer | Sí | Identificador lógico único (clave de negocio para `MERGE`). |

### 3.2. `Restaurante`

Establecimientos gastronómicos de la plataforma.

| Propiedad (enunciado) | Nombre técnico | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| Nombre | `nombre` | String | Sí | Nombre del restaurante. |
| Año de Apertura | `anio_apertura` | Integer | Sí | Año en que abrió (p. ej. 1990–2025). |
| Rango de Precios | `rango_precios` | String (enum) | Sí | `Económico`, `Moderado`, `Caro`, `Premium`. |
| Descripción | `descripcion` | String | No | Texto libre descriptivo. |
| — (técnico) | `restaurante_id` | Integer | Sí | Identificador lógico único. |

### 3.3. `TipoCocina`

Categorías gastronómicas.

| Propiedad (enunciado) | Nombre técnico | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| Nombre del Tipo | `nombre` | String | Sí | P. ej. `Italiana`, `Japonesa`; **único**. |
| Descripción | `descripcion` | String | No | Texto libre descriptivo. |
| — (técnico) | `tipo_cocina_id` | Integer | Sí | Identificador lógico único. |

### 3.4. `Chef`

Personas que lideran la preparación culinaria.

| Propiedad (enunciado) | Nombre técnico | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| Nombre | `nombre` | String | Sí | Nombre completo del chef. |
| Fecha de Nacimiento | `fecha_nacimiento` | Date | Sí | Formato ISO `YYYY-MM-DD`. |
| Nacionalidad | `nacionalidad` | String | Sí | País de origen. |
| — (técnico) | `chef_id` | Integer | Sí | Identificador lógico único. |

### 3.5. `Platillo`

Preparaciones ofrecidas por los restaurantes.

| Propiedad (enunciado) | Nombre técnico | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| Nombre | `nombre` | String | Sí | Nombre del platillo. |
| Precio | `precio` | Float | Sí | Precio base de referencia (> 0). |
| Descripción | `descripcion` | String | No | Texto libre descriptivo. |
| — (técnico) | `platillo_id` | Integer | Sí | Identificador lógico único. |

---

## 4. Identificación de relaciones (aristas)

Se identifican **ocho tipos de relación**. La nomenclatura sigue la convención
del enunciado: **mayúsculas con guiones bajos**.

| Relación | Origen → Destino | Cardinalidad | Propiedades | Regla |
| :--- | :--- | :--- | :--- | :--- |
| `CALIFICÓ` | `Usuario` → `Restaurante` | N:M | `puntuacion` (1–5), `fecha`, `comentario` | RN1, RN4 |
| `VISITÓ` | `Usuario` → `Restaurante` | N:M | `fecha`, `consumo`, `con_reserva` | RN1 |
| `ES_AMIGO_DE` | `Usuario` → `Usuario` | N:M | `fecha_amistad` | RN6 |
| `PERTENECE_A` | `Restaurante` → `TipoCocina` | N:M | — | RN2 |
| `OFRECE` | `Restaurante` → `Platillo` | N:M | `precio`, `disponible` | RN2, RN5 |
| `PREPARA` | `Chef` → `Platillo` | N:M | `estilo`, `especialidad` | RN3 |
| `TRABAJA_EN` | `Chef` → `Restaurante` | N:M | `fecha_inicio`, `puesto` | RN3 |
| `LE_GUSTA` | `Usuario` → `TipoCocina` | N:M | `nivel_interes` (1–5) | RN6 (perfil declarado) |

### 4.1. Detalle de propiedades de las relaciones

| Relación | Propiedad | Tipo | Obligatorio | Descripción / dominio |
| :--- | :--- | :--- | :-: | :--- |
| `CALIFICÓ` | `puntuacion` | Integer | Sí | Estrellas de 1 a 5 (RN4). |
| `CALIFICÓ` | `fecha` | Date | Sí | Fecha de la calificación. |
| `CALIFICÓ` | `comentario` | String | No | Texto libre del usuario. |
| `VISITÓ` | `fecha` | Date | Sí | Fecha de la visita. |
| `VISITÓ` | `consumo` | Float | Sí | Monto consumido (moneda de la plataforma). |
| `VISITÓ` | `con_reserva` | Boolean | Sí | `true` si la visita se hizo con reserva. |
| `ES_AMIGO_DE` | `fecha_amistad` | Date | Sí | Fecha desde la que son amigos. |
| `OFRECE` | `precio` | Float | Sí | Precio de ese platillo en ese restaurante. |
| `OFRECE` | `disponible` | Boolean | Sí | `true` si está actualmente disponible. |
| `PREPARA` | `estilo` | String | No | Estilo de preparación del chef. |
| `PREPARA` | `especialidad` | Boolean | No | `true` si el chef es especialista en ese platillo. |
| `TRABAJA_EN` | `fecha_inicio` | Date | Sí | Fecha de inicio en el restaurante. |
| `TRABAJA_EN` | `puesto` | String | No | Cargo (p. ej. `Chef Ejecutivo`, `Sous Chef`). |
| `LE_GUSTA` | `nivel_interes` | Integer | Sí | Interés declarado de 1 a 5. |

---

## 5. Modelo conceptual de grafos

### 5.1. Diagrama conceptual

```mermaid
flowchart LR
    U([Usuario]):::n
    R([Restaurante]):::n
    T([TipoCocina]):::n
    C([Chef]):::n
    P([Platillo]):::n

    U -- "CALIFICÓ {puntuacion, fecha, comentario}" --> R
    U -- "VISITÓ {fecha, consumo, con_reserva}" --> R
    U -- "ES_AMIGO_DE {fecha_amistad}" --> U
    U -- "LE_GUSTA {nivel_interes}" --> T
    R -- "PERTENECE_A" --> T
    R -- "OFRECE {precio, disponible}" --> P
    C -- "TRABAJA_EN {fecha_inicio, puesto}" --> R
    C -- "PREPARA {estilo, especialidad}" --> P

    classDef n fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px,color:#111;
```

Leyenda: cada nodo representa una **entidad**; cada arco una **relación dirigida**
con sus **propiedades**. El grafo es **heterogéneo** (nodos de distinto tipo) y
**mixto** en dirección (relaciones entre entidades distintas y autorrelación
`ES_AMIGO_DE`).

### 5.2. Lectura del modelo (patrones de traversal relevantes)

| Patrón de traversal | Relaciones implicadas | Consulta de negocio soportada |
| :--- | :--- | :--- |
| `Usuario -[:ES_AMIGO_DE*1..3]-> Usuario -[:CALIFICÓ]-> Restaurante` | Amistad + Calificación | Recomendación social (Q1). |
| `Chef -[:TRABAJA_EN]-> Restaurante <-[:CALIFICÓ]- Usuario` y `Chef -[:PREPARA]-> Platillo <-[:OFRECE]- Restaurante` | Trabajo, preparación, oferta | Chefs de alto impacto (Q2). |
| `Usuario -[:VISITÓ]-> Restaurante` (agregación `con_reserva`, `puntuación`) | Visita + Calificación | Restaurantes infravalorados (Q3). |
| `Restaurante -[:VISITÓ|VISITÓ]-`... `(consumo)` vs `rango_precios` | Visita + atributo del restaurante | Precio declarado vs. consumo real (Q4). |
| `Usuario -[:LE_GUSTA]-> TipoCocina` vs `Usuario -[:VISITÓ]-> Restaurante -[:PERTENECE_A]-> TipoCocina` | Preferencia declarada vs. comportamiento | Discrepancia cocina declarada vs. visitada (Q5). |
| `Usuario -[:ES_AMIGO_DE*]-> Usuario` (`shortestPath`) | Amistad | Grados de separación (N1). |
| `Restaurante <-[:TRABAJA_EN]- Chef` + `Restaurante -[:OFRECE]-> Platillo` | Trabajo + oferta | Restaurantes altamente conectados (N2). |

---

## 6. Justificación del enfoque de grafos

| Necesidad del negocio | Ventaja del modelo de grafos |
| :--- | :--- |
| Recomendación basada en amigos a 3 grados | `ES_AMIGO_DE*1..3` expresa el traversal de longitud variable en una sola cláusula. |
| Chefs que conectan restaurantes y platillos | El traversal `Chef → Restaurante → ... → Platillo` es natural y de costo proporcional al vecindario. |
| Comparar preferencia declarada vs. comportamiento | Dos caminos alternativos desde `Usuario` (`LE_GUSTA` vs `VISITÓ→PERTENECE_A`) se contrastan sin `JOIN`s. |
| Grados de separación | `shortestPath` sobre la red social es un algoritmo nativo del grafo. |
| Datos heterogéneos y en evolución | El modelo *schema-less* añade propiedades y relaciones sin migraciones. |

El modelo relacional exigiría múltiples tablas puente, `JOIN`s de N niveles y
recursividad SQL para las mismas consultas; el grafo lo expresa de forma directa.

---

## 7. Catálogo conceptual de consultas de negocio

En esta fase se define **qué debe responder el sistema**; la implementación
Cypher se aborda en la Fase 5. Se distinguen 5 consultas obligatorias (Q1–Q5) y
2 análisis de redes (N1–N2).

### 7.1. Consultas obligatorias

| ID | Consulta | Datos de entrada | Resultado esperado | Reglas |
| :-: | :--- | :--- | :--- | :--- |
| **Q1** | Recomendar restaurantes según calificaciones altas (≥ 4) de amigos directos e indirectos (hasta 3 grados), excluyendo los ya visitados. | `email` (o `usuario_id`) | Restaurantes ordenados por nº de amigos coincidentes y calificación promedio de esos amigos. | RN6 |
| **Q2** | Identificar chefs de alto impacto: trabajan en restaurantes con calificación promedio > 4 y sus platillos se ofrecen en ≥ 3 restaurantes distintos. | — (global) | Lista de chefs con métricas (`prom_restaurantes`, `num_restaurantes_platillos`). | RN3 |
| **Q3** | Encontrar restaurantes infravalorados: tasa de visitas con reserva > promedio general, pero calificación promedio < promedio general. | — (global) | Restaurantes con `tasa_reserva`, `prom_rating`, referencias a promedios globales. | RN1 |
| **Q4** | Comparar el rango de precios declarado contra el consumo promedio real de sus visitas; hallar mayor diferencia. | — (global) | Restaurantes ordenados por diferencia (`consumo_real − consumo_esperado`). | RN1, S3 |
| **Q5** | Detectar discrepancia entre el tipo de cocina favorito declarado (`LE_GUSTA` máximo) y el realmente visitado más frecuente (`VISITÓ→PERTENECE_A`). | — (global) | Usuarios con `cocina_declarada`, `cocina_real` y bandera de discrepancia. | RN2 |

### 7.2. Análisis de redes

| ID | Análisis | Método | Resultado esperado |
| :-: | :--- | :--- | :--- |
| **N1** | Rutas más cortas entre usuarios (grados de separación). | `shortestPath` sobre `ES_AMIGO_DE`. | Longitud del camino (nº de saltos) y camino entre dos usuarios. |
| **N2** | Restaurantes altamente conectados (más chefs y platillos destacados). | Grado de entrada/salida sobre `TRABAJA_EN` y `OFRECE`. | Ranking de restaurantes con `num_chefs` y `num_platillos`. |

### 7.3. Preguntas de negocio → elementos del modelo

| Consulta | Nodos usados | Relaciones usadas | Propiedades clave |
| :-: | :--- | :--- | :--- |
| Q1 | `Usuario`, `Restaurante` | `ES_AMIGO_DE`, `CALIFICÓ`, `VISITÓ` | `puntuacion`, `email` |
| Q2 | `Chef`, `Restaurante`, `Platillo` | `TRABAJA_EN`, `PREPARA`, `OFRECE`, `CALIFICÓ` | `puntuacion` |
| Q3 | `Restaurante`, `Usuario` | `VISITÓ`, `CALIFICÓ` | `con_reserva`, `puntuacion` |
| Q4 | `Restaurante`, `Usuario` | `VISITÓ` | `rango_precios`, `consumo` |
| Q5 | `Usuario`, `TipoCocina`, `Restaurante` | `LE_GUSTA`, `VISITÓ`, `PERTENECE_A` | `nivel_interes` |
| N1 | `Usuario` | `ES_AMIGO_DE` | — |
| N2 | `Restaurante`, `Chef`, `Platillo` | `TRABAJA_EN`, `OFRECE` | — |

---

## 8. Trazabilidad requerimiento → modelo

| Requerimiento del enunciado | Cubierto por |
| :--- | :--- |
| Modelado natural de relaciones | Secciones 3, 4 y 5 (5 nodos, 8 relaciones, propiedades en nodos y aristas). |
| Consultas eficientes multi-nivel | Patrones de traversal (§5.2) y catálogo de consultas (§7). |
| Análisis de redes | N1 (`shortestPath`) y N2 (restaurantes conectados). |
| Recomendaciones inteligentes | Q1 (social), Q2 (chefs), Q4/Q5 (patrones de consumo). |
| Reglas de negocio | §2.3 y su mapeo en §4. |
| Convenciones de nombres | Etiquetas singular/CamelCase; relaciones MAYÚSCULAS_CON_GUIONES. |

---
