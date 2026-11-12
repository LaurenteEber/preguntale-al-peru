# Plan de implementación por slices

**9/11/2026.** Los slices 1 a 3 están hechos y el servicio responde desde el celular con el motor por intenciones sobre el cubo precalculado.

Desde el 8/11/2026 el dueño decidió construir el **motor de inferencia a pedido**: calcula desde las preguntas de los cuestionarios de la ENDES y la ENAHO. Su diseño está en `docs/diseno/motor_inferencia.md` y sus tecnologías en `docs/diseno/tecnologias.md`.

La **beta cerrada** (antes slice 4) queda en pausa y su contenido pasa al slice M4 (R-07). Cada slice deja algo usable de punta a punta y no rompe lo anterior. Q1–Q4 y el cubo `010ea965` son la regresión de todos.

| Slice | Qué podrá hacer el usuario o el proyecto al terminar | Fase del diseño | Depende de |
|---|---|---|---|
| 1. Motor por intenciones | Hecho el 3/11/2026 (`slice-1/`) | — | — |
| 2. Intérprete de preguntas | Hecho el 5/11/2026 (`slice-2/`) | — | — |
| 3. API y web mínima | Hecho el 7/11/2026 (`slice-3/`) | — | — |
| **M0. Cimientos del motor** | El proyecto calcula desde los microdatos de la ENDES 2024: índice de variables completo, tablas del diseño muestral, ejecutor con compuertas y las recetas de anemia y desnutrición crónica, que igualan al cubo. Nada cambia para el usuario | 0 | Diseño aprobado; ZIP de la ENDES 2024 bajados por el dueño |
| **M1. Planificador (spike)** | El motor responde **a la sombra** preguntas nuevas sobre la ENDES 2024 (niño, mujer y hogar): elige el dato, pregunta cuando hay dudas o dice «no puedo» con alternativas. Se mide qué tan bien lo hace con unas 100 preguntas | 1 | M0 |
| **M2. ENDES completa** | El motor cubre la ENDES 2015–2025: series, comparaciones entre años y «¿cuántos?» derivado (X-24); umbrales exigibles en la prueba no vista | 2 | M1; respaldo de los crudos probado |
| **M3. ENAHO** | El motor cubre la ENAHO 2015–2025 en corte transversal: pobreza por receta, medias, razones y medianas descriptivas | 3 | M2 |
| **M4. Integración y beta** | El usuario recibe en la web las respuestas del motor nuevo, tema por tema. Despliegue, dominio y HTTPS, y prueba con personas de fuera (P-05) | 4 | M3; resto de X-05; X-07 |
| **M5. Panel ENAHO** | Preguntar por transiciones: cuántos hogares salieron de la pobreza y cuántos cayeron | 5 | M4; F-02 y X-23 |
| Ola 1 | Temas nuevos de otras fuentes (antes slice 5) | después de la beta | M4; GA-13; X-06 |

## Slices hechos

| Slice | Etiqueta | Cierre |
|---|---|---|
| 1 | `slice-1-cerrado`, `slice-1-adenda-cerrada` | `slice-1/evidencia/cierre.md` |
| 2 | `slice-2-cerrado` | `slice-2/evidencia/cierre.md` |
| 3 | `slice-3-cerrado` | `slice-3/evidencia/cierre.md` |
| M0 | `slice-m0-cerrado` (12/11/2026) | `slice-m0/evidencia/cierre.md` |

## M0 — Cimientos del motor

- **Backlog:** `slice-m0/`.
- **Problema:** hoy las cifras de encuesta salen de un cubo con 4 indicadores. Para calcular a pedido hacen falta:
  - los microdatos completos;
  - un índice de todas las variables;
  - tablas que digan cómo pesar cada archivo;
  - un ejecutor seguro y con compuertas.
- **Entrega:**
  - decisiones, reglas y `agents.md` actualizados;
  - auditoría de seguridad de lo que entra, con controles automáticos;
  - ZIP de la ENDES 2024 registrados y respaldados en el repo privado de crudos, con restauración probada y liberación del espacio local;
  - conversor a Parquet e índice de variables;
  - tablas curadas de 2024;
  - gramática y DuckDB endurecido;
  - ejecutor con pool, compuertas y verificador en R;
  - `svy` 0.35.0;
  - las recetas de anemia (dos criterios) y desnutrición crónica de 2024 desde los microdatos.
- **Fuera:** el LLM, la búsqueda, la web y otros años.
- **Hecho cuando:**
  - las recetas de 2024 igualan las 90 filas de 2024 del cubo (redondeadas a 8 decimales, |dif| ≤ 1e-8; casos y gl idénticos);
  - el índice está completo al 100 %;
  - el ejecutor coincide con R en el microdato sintético;
  - las compuertas dan el mismo estado que el validador actual;
  - el tamaño (ZIP y Parquet) y los tiempos están medidos en el Mac;
  - las dependencias tienen su auditoría aprobada;
  - la suite está en verde.

## M1 — Planificador (spike)

- **Backlog:** `slice-m1/` (detallado el 12/11/2026; **en curso** en la rama `slice-m1`).
- **Frente de datos en paralelo:** backlog aparte, pendiente; no entra en M1.
- **Entrega:**
  - enriquecimiento del índice (texto de las preguntas, universos, ventanas, sujetos);
  - intérprete en modo motor;
  - recuperador (`bm25s` + e5-small);
  - planificador;
  - verificador, huellas y decisión;
  - aclaraciones con `id_plan`;
  - sustitución y alternativas;
  - sellos;
  - contrato v2;
  - caché y costo;
  - modo sombra;
  - conjunto de evaluación de unas 100 preguntas.
- **Hecho cuando:**
  - las métricas del §23.3 del diseño están informadas con su intervalo;
  - el p95 por etapa está medido;
  - el número de muestras está decidido;
  - el modo sombra corre sin errores sobre Q1–Q4 y la matriz.

## M2 a M5 (esbozo; se detallan al cerrar el anterior)

- **M2 — ENDES completa:**
  - descarga, respaldo en el repo privado e índice 2015–2025, por bloques (un año a la vez), liberando los ZIP de cada bloque ya restaurado;
  - `perfil_anual.csv` y `relacion_entre_anios.csv` completos;
  - recetas de toda la serie con la regresión completa del cubo;
  - conceptos armonizados con cifra oficial o con demanda;
  - comparaciones entre años (apilado);
  - «¿cuántos?» derivado (X-24);
  - conjunto de evaluación ≥ 150 preguntas y umbrales exigibles.
- **M3 — ENAHO:**
  - ENAHO 2015–2025: sumaria y archivos de persona y hogar, por bloques como en M2;
  - antes de empezar: K-08 (si los Parquet de la ENAHO pueden publicarse);
  - receta de pobreza que iguala al cubo;
  - medias, razones de totales y medianas descriptivas (§15.3 del diseño);
  - totales con la ENAHO (R-ENC-17).
- **M4 — Integración y beta.** Incluye lo que tenía el antiguo slice 4:
  - temas en `nuevo`, uno por uno, con el modo sombra en verde;
  - formulario guiado ampliado;
  - concurrencia medida con 5 y 10 clientes;
  - despliegue, dominio y HTTPS: revisar que la imagen escucha en todas las interfaces y las cabeceras de proxy para la IP (W-09);
  - contadores de límites fuera de memoria;
  - medir el candado del motor y la traza de errores sin el texto de la pregunta;
  - P-03: los nombres de personas en la pregunta;
  - X-05, X-07 y X-01;
  - **antes de que entre gente de fuera:** H-M (quitar «o más bajo» del formulario, del intérprete y del error) y H-N (rótulos «¿Sirvió lo que se gastó?» y «Ver el gasto junto con el problema», con textos aprobados por el dueño);
  - un conjunto de evaluación no visto para la web (H-E); puede reutilizar el 30 % no visto del conjunto de M1–M2;
  - pendientes menores del slice 3: saltos de línea en el registro de accesos, el aviso de «listo» de `pap servir` y la altitud del SIEN (H-G, espera W-04);
  - una historia de mantenimiento con H-O a H-S (mensaje viejo de `bajar_biblioteca.sh`, archivos `._*` en el release, `estado.md`, la prueba sensible a `ANTHROPIC_BASE_URL` y el «factor 1,0000000» de la cita);
  - restricción: el tope de 125 palabras de la capa 1 (R-04), midiendo el peor caso antes de agregar texto;
  - prueba con usuarios de fuera, con un criterio medible: número de personas, porcentaje que entiende la cifra y sus límites, y 0 lecturas erróneas graves.
- **M5 — Panel ENAHO:** según el §25 del diseño, después de F-02 y X-23.
