# Sistema de Recomendación de Restaurantes con Neo4j

---

## 1. Marco Formativo

### 1.1. Valor
| Nombre del valor | ¿Cómo se aplica en tu laboratorio? |
| :--- | :--- |
| Responsabilidad | Los estudiantes son responsables de diseñar e implementar correctamente el modelo de grafos en Neo4j, garantizando la integridad de las relaciones, la eficiencia de las consultas Cypher y la aplicación correcta de algoritmos de análisis de redes para el sistema de recomendación desarrollado. |

### 1.2. Competencia(s)
| Tipo de Competencia | Descripción |
| :--- | :--- |
| **Competencia General** | Construye soluciones integrales trabajando en forma colaborativa y propositiva en equipos interdisciplinarios, en forma presencial o utilizando plataformas virtuales. |
| **Competencia Específica** | Implementa técnicas de modelado de datos basadas en grafos utilizando Neo4j para diseñar sistemas de recomendación eficientes, aplicando el lenguaje de consultas Cypher, algoritmos de análisis de rutas más cortas y técnicas de modelado de relaciones complejas para resolver problemas de conectividad y análisis de redes sociales. |

---

## 2. Resumen Ejecutivo
Este proyecto está diseñado para que los estudiantes apliquen de manera integral sus competencias en el diseño, implementación y consulta de bases de datos de grafos utilizando Neo4j. El desafío central consiste en construir un sistema de recomendación de restaurantes basado en las preferencias de los usuarios, sus relaciones sociales y patrones de visita, aprovechando la capacidad de Neo4j para modelar y consultar relaciones complejas de forma eficiente.

A partir del análisis de los requerimientos del negocio, los estudiantes deberán diseñar y documentar un modelo de grafos que represente usuarios, restaurantes, tipos de cocina, chefs y platillos, junto con sus relaciones (calificaciones, visitas, amistades, preparación, oferta de platillos). Un requisito fundamental de este proyecto es aprovechar las ventajas de las bases de datos de grafos, utilizando propiedades en nodos y aristas para enriquecer el modelo de datos.

Una vez definido el modelo, los estudiantes procederán a su implementación en Neo4j, creando nodos con sus propiedades y estableciendo las relaciones correspondientes. Esta fase incluye la configuración de la base de datos, la carga de un conjunto significativo de datos y la implementación de consultas Cypher esenciales que respondan a las necesidades del negocio. Además, deberán aplicar análisis básicos de redes para calcular rutas más cortas entre usuarios e identificar restaurantes altamente conectados en el sistema.

---

## 3. Enunciado del Proyecto

### 3.1. Descripción del problema a resolver
Los estudiantes diseñarán e implementarán una base de datos de grafos en Neo4j, optimizada para un sistema de recomendación de restaurantes que considera tanto las preferencias individuales como las conexiones sociales entre usuarios. El problema principal consiste en modelar las relaciones complejas entre usuarios, restaurantes, tipos de cocina, chefs y platillos de forma natural y eficiente, aprovechando las ventajas de las bases de datos de grafos.

El sistema deberá garantizar:
* **Modelado natural de relaciones:** Representación intuitiva de conexiones entre entidades (usuarios, restaurantes, chefs, tipos de cocina, platillos).
* **Consultas eficientes:** Uso de Cypher para consultas que atraviesan múltiples niveles de relaciones.
* **Análisis de redes:** Aplicación de algoritmos para encontrar patrones de conexión, rutas más cortas y comunidades.
* **Recomendaciones inteligentes:** Generación de sugerencias basadas en chefs compartidos, historial de calificaciones y patrones de consumo/reserva.

#### Entidades principales del sistema:
* **Usuario:** Personas que utilizan la plataforma. De cada usuario se debe guardar: `Nombre`, `Email`, `Edad`, `País`.
* **Restaurante:** Establecimiento gastronómico disponible en la plataforma. De cada restaurante se debe guardar: `Nombre`, `Año de Apertura`, `Rango de Precios`, `Descripción`.
* **TipoCocina:** Categorías gastronómicas. De cada tipo de cocina se debe guardar: `Nombre del Tipo`, `Descripción`.
* **Chef:** Personas que lideran la preparación culinaria. De cada chef se debe guardar: `Nombre`, `Fecha de Nacimiento`, `Nacionalidad`.
* **Platillo:** Preparaciones ofrecidas por los restaurantes. De cada platillo se debe guardar: `Nombre`, `Precio`, `Descripción`.

#### Relaciones del sistema:
* `CALIFICÓ`: Un usuario califica un restaurante (con propiedades: `puntuación` [1-5], `fecha`, `comentario`).
* `VISITÓ`: Un usuario visitó un restaurante (con propiedades: `fecha de visita`, `consumo`, `con_reserva` [true/false]).
* `ES_AMIGO_DE`: Relación de amistad entre usuarios (con propiedades: `fecha de amistad`).
* `PERTENECE_A`: Un restaurante pertenece a uno o más tipos de cocina.
* `OFRECE`: Un restaurante ofrece un platillo (con propiedades: `precio`, `disponible` [true/false]).
* `PREPARA`: Un chef prepara un platillo (con propiedades: `estilo`, `especialidad`).
* `TRABAJA_EN`: Un chef trabaja en un restaurante (con propiedades: `fecha_inicio`, `puesto`).
* `LE_GUSTA`: Un usuario tiene preferencia por un tipo de cocina (con propiedades: `nivel de interés` [1-5]).

#### Reglas de negocio del sistema:
1. Un usuario puede calificar y visitar múltiples restaurantes.
2. Un restaurante puede pertenecer a varios tipos de cocina y ofrecer múltiples platillos.
3. Un chef puede trabajar en varios restaurantes a lo largo del tiempo y preparar múltiples platillos.
4. Las calificaciones deben estar en el rango de 1 a 5 estrellas.
5. Un restaurante no puede ofrecer el mismo platillo más de una vez.
6. El sistema debe poder recomendar restaurantes a un usuario basándose en las calificaciones altas que sus amigos (directos e indirectos, hasta 3 grados de separación) han dado a restaurantes que el usuario aún no ha visitado.

---

### 3.2. Alcance del proyecto

#### Alcance obligatorio:
* Diseñar un modelo de grafos conceptual que represente todas las entidades y relaciones del sistema.
* Implementar el modelo en Neo4j, creando todos los nodos con sus propiedades correspondientes.
* Establecer todas las relaciones entre nodos con sus propiedades.
* Insertar al menos **500 usuarios, 200 restaurantes, 100 chefs, 50 platillos y 15 tipos de cocina**, con sus respectivas relaciones.
* Implementar consultas Cypher eficientes para:
  * Recomendar restaurantes a un usuario basándose en las calificaciones altas ($\ge 4$) que sus amigos, directos e indirectos (hasta 3 grados de separación), han dado, priorizando por cantidad de amigos coincidentes y calificación promedio de dichos amigos, excluyendo restaurantes que el usuario ya visitó.
  * Identificar chefs de alto impacto: aquellos que trabajan en restaurantes con calificación promedio superior a 4 estrellas y cuyos platillos son ofrecidos en al menos 3 restaurantes distintos.
  * Encontrar restaurantes "infravalorados": aquellos con una tasa de visitas con reserva superior al promedio general, pero con calificación promedio por debajo del promedio general de la plataforma.
  * Comparar el rango de precios declarado de cada restaurante contra el consumo promedio real registrado en sus visitas, identificando los restaurantes cuya diferencia entre el consumo real y lo esperado para su categoría de precio sea mayor.
  * Detectar discrepancias entre el tipo de cocina favorito declarado por cada usuario (`LE_GUSTA` con mayor nivel de interés) y el tipo de cocina que realmente visita con mayor frecuencia (según `VISITÓ` $\rightarrow$ `PERTENECE_A`).
* Aplicar análisis de redes para:
  * Calcular rutas más cortas entre usuarios (grados de separación).
  * Identificar restaurantes altamente conectados (con más chefs y platillos destacados).
* Documentar el proceso de diseño, implementación y los resultados de las consultas.

#### Alcance opcional:
* Implementar búsqueda de comunidades de usuarios por patrones de visita y consumo.
* Implementar algoritmos de centralidad para identificar usuarios influyentes.
* Aplicar filtrado colaborativo basado en grafos para mejorar las recomendaciones.
* Analizar cadenas de recomendaciones transitivas basadas en chefs compartidos.

---

### Requerimientos técnicos
Los estudiantes utilizarán Neo4j como motor de base de datos de grafos para el diseño, creación y manipulación de los datos. Se podrá utilizar Python para la generación y carga masiva de datos mediante scripts automatizados.

#### Modelado de datos en Neo4j:
* Identificar todas las entidades como nodos con sus propiedades correspondientes.
* Definir las relaciones (aristas) entre nodos con propiedades que enriquezcan el modelo.
* Aplicar convenciones de nombres: nodos con etiquetas en singular y CamelCase (`Usuario`, `Restaurante`, `TipoCocina`, `Chef`, `Platillo`), relaciones en mayúsculas con guiones bajos (`CALIFICÓ`, `VISITÓ`, `ES_AMIGO_DE`, `PERTENECE_A`, `OFRECE`, `PREPARA`, `TRABAJA_EN`, `LE_GUSTA`).
* Utilizar propiedades tanto en nodos como en relaciones para almacenar información relevante.
* Diseñar el modelo pensando en las consultas de negocio que se deben responder.

#### Implementación en Neo4j:
* Instalar y configurar Neo4j Desktop o Neo4j Community Edition.
* Crear la base de datos del proyecto con configuraciones adecuadas.
* Implementar el modelo de grafos mediante comandos Cypher `CREATE`.
* Insertar datos de prueba representativos que permitan validar todas las funcionalidades.

#### Consultas Cypher:
* Implementar todas las consultas requeridas por el negocio de forma eficiente.
* Utilizar patrones de Cypher (`MATCH`, `WHERE`, `CREATE`, `MERGE`, `SET`, `RETURN`).
* Aplicar funciones de agregación (`COUNT`, `AVG`, `SUM`) cuando sea necesario.
* Implementar consultas que atraviesen múltiples niveles de relaciones.
* Documentar el propósito y resultado de cada consulta implementada.

#### Análisis de redes y algoritmos:
* Implementar consultas para calcular la ruta más corta entre usuarios (`shortestPath`).
* Identificar restaurantes altamente conectados (con más chefs y platillos destacados).

#### Carga masiva de datos:
* Utilizar el comando `LOAD CSV` de Cypher para insertar datos de forma masiva desde archivos CSV.
* Crear archivos CSV bien estructurados para cada tipo de nodo y relación.
* Utilizar `MERGE` para evitar duplicados en la creación de nodos.
* Implementar transacciones por lotes (`USING PERIODIC COMMIT`) para optimizar el rendimiento.
* Validar la integridad de los datos insertados.
* Opcionalmente, se puede utilizar Python con la librería `neo4j-driver` si el estudiante lo prefiere.

---

### 3.3. Entregables

| Tipo | Descripción |
| :--- | :--- |
| **Prototipo** | Base de datos Neo4j funcional con todos los datos cargados, relaciones establecidas y consultas operativas que demuestren el sistema de recomendación. |
| **Documentación Técnica** | Manual técnico que incluya: modelo conceptual de grafos (diagrama visual de nodos y relaciones), descripción de todas las propiedades de nodos y relaciones, script Cypher completo de creación del esquema, documentación de todas las consultas implementadas con ejemplos y resultados, y análisis de las ventajas de usar Neo4j para este problema. |
| **Código Fuente** | Código completo del proyecto, incluyendo: scripts Cypher de creación del modelo, archivos CSV con los datos, scripts Cypher con comandos `LOAD CSV` para la carga masiva (o scripts Python si se optó por esa alternativa), consultas Cypher organizadas por funcionalidad, y estructura clara con comentarios explicativos. |
| **Manual de Usuario** | Documento que explica: cómo instalar y configurar Neo4j, cómo cargar los datos iniciales usando `LOAD CSV` (o el método alternativo utilizado), cómo ejecutar cada consulta implementada con ejemplos prácticos, interpretación de los resultados de las consultas de recomendación, y resolución de problemas comunes. |
| **Repositorio** | Deberán crear un repositorio en GitHub con el nombre `BD2_2S26_Proyectos_carnet` y crear la carpeta `"Segundo Proyecto"` donde harán la entrega de estos entregables. |

---

## 4. Metodología

* **Fase 1: Análisis de Requerimientos y Modelado Conceptual**  
  Los estudiantes analizarán los requerimientos del sistema de recomendación de restaurantes, identificando las entidades principales (nodos), sus atributos (propiedades) y las relaciones entre ellas (aristas). Diseñarán el modelo conceptual de grafos considerando cómo las conexiones entre usuarios, restaurantes, chefs, tipos de cocina y platillos permiten generar recomendaciones. Definirán las consultas más importantes que el sistema debe responder.

* **Fase 2: Diseño del Modelo de Grafos para Neo4j**  
  Transformarán el modelo conceptual en un esquema implementable en Neo4j. Definirán las etiquetas de los nodos (`Usuario`, `Restaurante`, `TipoCocina`, `Chef`, `Platillo`) y sus propiedades. Especificarán los tipos de relaciones (`CALIFICÓ`, `VISITÓ`, `ES_AMIGO_DE`, `PERTENECE_A`, `OFRECE`, `PREPARA`, `TRABAJA_EN`, `LE_GUSTA`) con sus propiedades correspondientes. Diseñarán el esquema considerando las consultas de negocio, optimizando la estructura para facilitar el traversal del grafo y el análisis de patrones.

* **Fase 3: Configuración de Neo4j e Implementación Física**  
  Instalarán y configurarán Neo4j Desktop o Community Edition en su entorno de desarrollo. Crearán la base de datos del proyecto con las configuraciones apropiadas. Implementarán el modelo de grafos mediante scripts Cypher, creando constraints y índices necesarios para garantizar integridad y rendimiento.

* **Fase 4: Carga Masiva de Datos**  
  Prepararán archivos CSV con los datos de al menos 500 usuarios, 200 restaurantes, 100 chefs, 50 platillos y 15 tipos de cocina con sus respectivas relaciones. Utilizarán el comando `LOAD CSV` de Cypher para realizar la inserción masiva de datos, aplicando `MERGE` para evitar duplicados y `USING PERIODIC COMMIT` para optimizar el rendimiento en grandes volúmenes. Como alternativa, pueden utilizar scripts en Python con la librería `neo4j-driver` si lo prefieren. Verificarán la correcta inserción de nodos y relaciones mediante consultas de validación.

* **Fase 5: Implementación de Consultas Cypher**  
  Implementarán las 5 consultas esenciales requeridas por el negocio utilizando el lenguaje Cypher: recomendación social basada en calificaciones de amigos hasta 3 grados de separación, identificación de chefs de alto impacto, restaurantes infravalorados (alta reserva, baja calificación), comparación entre rango de precio declarado y consumo real, y discrepancia entre cocina favorita declarada y cocina realmente visitada. Documentarán cada consulta con su propósito, parámetros y resultados esperados.

* **Fase 6: Análisis de Redes y Documentación**  
  Aplicarán 2 análisis de redes: calcular rutas más cortas entre usuarios (grados de separación) e identificar restaurantes altamente conectados (con más chefs y platillos destacados). Documentarán los resultados obtenidos, incluyendo visualizaciones del grafo, métricas de análisis, ejemplos de recomendaciones generadas y conclusiones sobre las ventajas de usar Neo4j para este tipo de problemas.

---

## 5. Recursos y herramientas a utilizar

### Software de Base de Datos:
* Neo4j Desktop (versión 5.x o superior) o Neo4j Community Edition.
* Neo4j Browser para visualización y ejecución de consultas Cypher.
* Neo4j Bloom (opcional) para visualización avanzada del grafo.

### Herramientas de Desarrollo:
* Editor de texto o herramientas de generación de datos para crear archivos CSV.
* Python (opcional, versión 3.8 o superior) para generación automática de datos CSV o carga mediante `neo4j-driver`.
* Librerías opcionales: `neo4j-driver`, `faker`, `random`, `csv`, `pandas`.
* Editor de código (Visual Studio Code, PyCharm) para scripts Cypher.

### Herramientas de Modelado:
* Arrows.app (herramienta especializada para modelado de grafos en Neo4j).
* Draw.io o Lucidchart para diagramas conceptuales.
* yEd Graph Editor para visualización de grafos complejos.

### Plataformas de Colaboración:
* GitHub para control de versiones del código.
* UEDI para entrega del proyecto.

### Lecturas Recomendadas:
* Documentación oficial de Neo4j: [https://neo4j.com/docs/](https://neo4j.com/docs/)
* Neo4j Graph Academy: cursos gratuitos sobre modelado y Cypher.
* Cypher Query Language Reference.
* Graph Algorithms: Practical Examples in Apache Spark and Neo4j.

---

## 6. Desarrollo de Habilidades Blandas

### 6.1. Autogestión y Desarrollo Autónomo:
* **Responsabilidad Integral:** Asunción total del ciclo de vida del proyecto, desde el análisis y diseño del modelo de grafos hasta la implementación en Neo4j, carga de datos, desarrollo de consultas Cypher y aplicación de algoritmos de análisis de redes.
* **Capacidad de Autoaprendizaje:** Investigación y resolución independiente de problemas técnicos encontrados durante el proceso de modelado en Neo4j, aprendizaje del lenguaje Cypher y aplicación de algoritmos de grafos.
* **Pensamiento Analítico:** Habilidad para identificar patrones de relaciones complejas, diseñar consultas eficientes que atraviesen el grafo y aplicar algoritmos de análisis de redes para resolver problemas de recomendación.
* **Comunicación Escrita y Documentación:** Capacidad para transmitir decisiones técnicas de diseño del modelo de grafos de forma clara y estructurada, justificando las elecciones de modelado y explicando los resultados de las consultas y análisis.
* **Gestión del Tiempo y Disciplina:** Organización autónoma de las fases de desarrollo para cumplir con los hitos establecidos, asegurando la calidad en cada etapa sin supervisión constante.

---

## 7. Cronograma

| Tipo | Fecha Inicio | Fecha Fin |
| :--- | :--- | :--- |
| **Asignación de Proyecto** | 29/09/26 | 13/09/26 |
| **Elaboración** | 29/09/26 | 13/09/26 |
| **Calificación** | 16/10/26 | 17/10/26 |

---

## 8. Rúbrica de Calificación

### Requisitos previos
Antes de la evaluación del proyecto, los estudiantes deben cumplir con los requisitos que se indican en esta sección:

| Tema | Descripción | Cumple (Sí/No) |
| :--- | :--- | :--- |
| **Modelo de grafos completo** | El diseño debe incluir todos los tipos de nodos (`Usuario`, `Restaurante`, `TipoCocina`, `Chef`, `Platillo`) con sus propiedades, y todas las relaciones requeridas (`CALIFICÓ`, `VISITÓ`, `ES_AMIGO_DE`, `PERTENECE_A`, `OFRECE`, `PREPARA`, `TRABAJA_EN`, `LE_GUSTA`) correctamente definidas. | |
| **Base de datos Neo4j funcional** | La base de datos debe estar implementada en Neo4j con todos los nodos y relaciones creadas, accesible mediante Neo4j Browser. | |
| **Carga masiva de datos** | El sistema debe contener al menos 500 usuarios, 200 restaurantes, 100 chefs, 50 platillos y 15 tipos de cocina y sus respectivas relaciones insertadas mediante `LOAD CSV` de Cypher (u opcionalmente mediante scripts Python con `neo4j-driver`). | |
| **Consultas Cypher obligatorias** | Se deben implementar las 5 consultas requeridas: recomendación social por calificaciones de amigos (hasta 3 grados), chefs de alto impacto, restaurantes infravalorados, comparación rango de precio vs. consumo real, y discrepancia cocina favorita vs. cocina realmente visitada. | |
| **Análisis de redes** | Se deben implementar los 2 análisis requeridos: rutas más cortas entre usuarios (grados de separación) y restaurantes altamente conectados (con más chefs y platillos destacados). | |
| **Documentación técnica obligatoria** | Se debe incluir documento técnico en PDF o markdown que contenga: diagrama del modelo de grafos, descripción de todas las propiedades, scripts Cypher de creación del esquema, documentación de consultas con ejemplos y análisis de ventajas de Neo4j. | |
| **Manual de usuario obligatorio** | Se debe incluir manual de usuario en PDF que explique la instalación de Neo4j, carga de datos, ejecución de consultas con ejemplos prácticos e interpretación de resultados. | |
| **Código fuente organizado** | El código debe estar estructurado en archivos lógicos (creación de modelo, archivos CSV, scripts `LOAD CSV`, consultas), con comentarios explicativos y nomenclatura consistente. | |

---

### Matriz de Evaluación Detallada (Punteo Máximo: 100)

| No. | Criterio de evaluación | Punteo máximo | Nivel de evaluación (Satisfactorio / Necesita mejorar) |
| :---: | :--- | :---: | :--- |
| **1** | **Habilidades** | **40** | |
| 1.1 | **Documentación Técnica** | 15 | **Satisfactorio (15-9 pts):** Presenta el proceso completo de diseño del modelo de grafos, incluyendo diagrama visual de nodos y relaciones, descripción detallada de todas las propiedades, justificación del modelo, scripts Cypher completos y análisis de ventajas de Neo4j para el problema.<br>**Necesita mejorar (8-0 pts):** Incompleta, no muestra el diagrama del modelo de grafos, carece de descripción de propiedades, no incluye scripts Cypher completos o no analiza las ventajas. |
| 1.2 | **Manual de Usuario** | 10 | **Satisfactorio (10-6 pts):** Explica claramente cómo instalar y configurar Neo4j, cómo cargar los datos iniciales, cómo ejecutar cada consulta Cypher con ejemplos prácticos y parámetros, y cómo interpretar los resultados.<br>**Necesita mejorar (5-0 pts):** Confuso, carece de pasos de instalación, no documenta adecuadamente las consultas Cypher, no incluye ejemplos prácticos o no explica la interpretación de resultados. |
| 1.3 | **Código Fuente Organizado** | 15 | **Satisfactorio (15-9 pts):** El código Cypher está bien estructurado en archivos lógicos (DDL de modelo, archivos CSV con datos, scripts `LOAD CSV` para carga masiva, consultas por funcionalidad), comentado adecuadamente, con nomenclatura consistente. El repositorio en GitHub cumple con la estructura solicitada.<br>**Necesita mejorar (8-0 pts):** Desorganizado, sin comentarios, con nomenclatura inconsistente, mezclando diferentes funcionalidades en un solo archivo o el repositorio no tiene la estructura solicitada. |
| **2** | **Conocimientos** | **60** | |
| 2.1 | **Modelo de Grafos Completo y Correcto** | 20 | **Satisfactorio (20-12 pts):** El modelo incluye todos los tipos de nodos requeridos (`Usuario`, `Restaurante`, `TipoCocina`, `Chef`, `Platillo`) con propiedades apropiadas, todas las relaciones especificadas (`CALIFICÓ`, `VISITÓ`, `ES_AMIGO_DE`, `PERTENECE_A`, `OFRECE`, `PREPARA`, `TRABAJA_EN`, `LE_GUSTA`) con sus propiedades correspondientes, y refleja correctamente las reglas de negocio.<br>**Necesita mejorar (11-0 pts):** Incompleto, faltan tipos de nodos o relaciones requeridas, propiedades mal definidas, relaciones sin propiedades o no refleja las reglas de negocio. |
| 2.2 | **Implementación en Neo4j y Carga de Datos** | 15 | **Satisfactorio (15-9 pts):** La base de datos está correctamente implementada en Neo4j con todos los nodos y relaciones creadas. Se han insertado al menos 500 usuarios, 200 restaurantes, 100 chefs, 50 platillos y 15 tipos de cocina con sus relaciones mediante `LOAD CSV` de Cypher (u opcionalmente scripts Python). Archivos CSV bien estructurados, datos coherentes que permiten validar todas las funcionalidades.<br>**Necesita mejorar (8-0 pts):** Errores de implementación, no se alcanzan las cantidades mínimas, nodos/relaciones mal creadas, datos inconsistentes, no se usó `LOAD CSV` u otro método válido, archivos CSV mal estructurados. |
| 2.3 | **Consultas Cypher Eficientes** | 15 | **Satisfactorio (15-9 pts):** Se implementan correctamente las 5 consultas requeridas (recomendación social por calificaciones de amigos hasta 3 grados, chefs de alto impacto, restaurantes infravalorados, comparación rango de precio vs. consumo real, y discrepancia cocina favorita vs. visitada). Eficientes, aprovechan patrones de traversal multi-nivel y caminos de longitud variable, documentadas.<br>**Necesita mejorar (8-0 pts):** Incompletas, no cubren todos los casos, errores de sintaxis/lógica, ineficientes (no aprovechan grafos) o carecen de documentación. |
| 2.4 | **Análisis de Redes y Algoritmos** | 5 | **Satisfactorio (5-3 pts):** Se implementan correctamente los 2 análisis requeridos: rutas más cortas entre usuarios (`shortestPath`) y restaurantes altamente conectados (con más chefs y platillos destacados). Ambos incluyen interpretación de resultados.<br>**Necesita mejorar (2-0 pts):** Falta alguno de los análisis, no funcionan correctamente, algoritmos mal implementados o carecen de interpretación de resultados. |
| 2.5 | **Calidad de las Recomendaciones** | 5 | **Satisfactorio (5-3 pts):** El sistema genera recomendaciones basándose correctamente en chefs compartidos, historial de calificaciones y patrones de visita. Relevantes, fundamentadas en el grafo y documentadas con ejemplos.<br>**Necesita mejorar (2-0 pts):** Las recomendaciones no funcionan correctamente, no se basan en el análisis del grafo, son irrelevantes o carecen de ejemplos documentados. |
| | **TOTAL** | **100** | |