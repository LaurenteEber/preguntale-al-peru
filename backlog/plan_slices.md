# Plan de implementación por slices

2/11/2026. Parte del piloto cerrado (Q1–Q4 por consultas escritas a mano, `docs/estado.md`) y llega a la beta cerrada. Cada slice deja algo usable de punta a punta y no rompe lo anterior: Q1–Q4 son la regresión de todos.

| Slice | Qué podrá hacer el usuario al terminar | Fase | Depende de |
|---|---|---|---|
| **1. Motor por intenciones** | Hacer cualquier pregunta *estructurada* (intención + tema + territorio + periodo) sobre los 9 indicadores del piloto, para cualquier territorio y año con datos, y recibir la respuesta por capas, validada. Si la pregunta es ambigua («Lima», un distrito homónimo), el motor pregunta en vez de adivinar | 5a | Reconstrucción con T-02 (S1-00) |
| **2. Intérprete de preguntas** | Escribir la pregunta en lenguaje natural; un LLM la traduce a la consulta estructurada del slice 1 (nunca calcula ni ve cifras, P-01); lo que no entiende o está fuera de alcance se responde con una aclaración o con «todavía no tenemos datos de eso» | 5b | Slice 1 (contrato de consulta); decisión del dueño sobre proveedor y costo del LLM |
| **3. API y web mínima** (hecho el 7/11/2026) | Usar el servicio desde el celular: una caja de pregunta, la respuesta por capas (visible, «Más contexto», «Para citar»), la versión de la biblioteca y enlaces a las fuentes oficiales | 5c | Slices 1–2; X-04 (intervalo visible) |
| **4. Beta cerrada** | Que un grupo pequeño de personas reales lo use en la nube. Antes: prueba con usuarios (P-05), revisión de lo provisional (X-05), despliegue completo (F-05) y medición de uso sin datos personales (P-03) | 5 | Slices 1–3; X-05 |
| **5. Ampliación de datos (Ola 1)** | Preguntar por temas nuevos. Cada tema entra como un sub-slice vertical: fuente aprobada → estandarizada → indicador con doradas → intenciones → web. Antes: GA-13 y la separación de ejecutoras mixtas (X-06) | después de la beta | Slices 1–4 |

## Slice 1 — Motor por intenciones

- **Problema:** hoy cada pregunta necesita su consulta y su plantilla escritas a mano (`tests/fixtures/consultas_piloto/q*.yaml`, `plantillas._q1…_q4`, con nombres como «Huancavelica» dentro del código).
- **Entrega:** una consulta mínima con esquema (la que producirá el LLM en el slice 2) → resolución determinista del territorio → planificador que arma las cifras según las decisiones → plantillas por intención con textos fijos en YAML → la misma respuesta por capas y el mismo validador.
- **Fuera:** LLM, web, datos nuevos, indicadores nuevos.
- **Hecho cuando:** Q1–Q4 salen por el motor por intenciones sin cambiar cifras ni semáforos; una matriz de cobertura automática (indicadores × intenciones × territorios) no tiene caídas, marcadores sin rellenar ni códigos internos; una revisión independiente de usuario da «apto».
- Backlog: `slice-1/`.

## Slice 2 — Intérprete de preguntas (hecho el 5/11/2026: `slice-2/evidencia/cierre.md`)

- Traducción pregunta → consulta mínima con salida estructurada y validación por esquema; reintento o aclaración si no valida.
- Conjunto de evaluación de ≥ 100 preguntas reales y reformuladas (incluye fuera de alcance, ambiguas y engañosas), con la consulta esperada; métrica: % de consultas exactas y 0 % de cifras inventadas.
- El LLM no recibe datos de la biblioteca ni redacta la respuesta: solo la consulta.
- Decisiones previas del dueño: proveedor y modelo, presupuesto mensual, qué se guarda de las preguntas (P-03).

## Slice 3 — API y web mínima (hecho el 7/11/2026: `slice-3/evidencia/`)

- FastAPI + DuckDB en solo lectura sobre el cubo precalculado (`stack_tecnologico.md`); respuesta en < 2 s **sin LLM**. Con texto libre, el LLM midió p95 2,7 s en el slice 2: S3-08 fija su objetivo, la página muestra «Buscando…» y el formulario guiado (sin LLM) es la vía rápida.
- Lo medido en el slice 2: US$ 0,0024 por pregunta con el caché del proveedor (US$ 0,018 sin caché); el tope diario de llamadas del slice 3 se calcula con eso.
- Nombres de personas en la pregunta (P-03, E-07 del slice 2): no se detectan; con la web en la red de la casa sigue aceptado; se revisa en el slice 4.
- Web móvil primero: capas como desplegables, confianza sin colores (R-05), cita y versión de la biblioteca; accesibilidad WCAG AA.
- Decisión previa: X-04 (qué intervalo se ve).

## Slice 4 — Beta cerrada (esbozo)

- Prueba con usuarios de los perfiles de la revisión de usuario; corrección de lo que no se entienda.
- Revisión de lo provisional (X-05) y validación con terceros del corrector (corpus de ≥ 40 oraciones).
- Despliegue de todo el proyecto en la nube con una imagen desde `uv.lock`; respaldo del almacén resuelto.
- **Despliegue, dominio y HTTPS:** hoy la web corre en local o en la red de la casa (`pap servir`, imagen Docker). Falta el servidor, el dominio y el certificado. La imagen escucha en todas las interfaces (S3-09-a): revisar qué se publica. Detrás de un proxy, la IP del límite sería la del proxy: pasar las cabeceras de proxy de uvicorn solo desde el servidor de confianza (W-09).
- **Contadores fuera de memoria:** el límite por IP y el tope diario del LLM se reinician con el servicio y no se comparten entre procesos; con varios procesos o reinicios habría que guardarlos fuera (y limpiar las IP vencidas del límite).
- **Candado y LLM con varios usuarios:** un candado deja pasar una pregunta a la vez; medir con varias personas a la vez (más aún con el LLM, p95 3,13 s en vivo) y decidir si hace falta otro diseño.
- **Revisión de P-03:** los nombres de personas escritos en la pregunta no se detectan (E-07); revisarlo antes de abrir a terceros, junto con la caché de 24 h.
- **X-05 y X-07 antes de que entre gente de fuera:** la revisión de lo provisional y el visto a las listas curadas de gasto. También X-01 si se quiere mostrar «¿Qué puedo hacer?» en la web.
- **Pendientes menores de la revisión del slice 3** (`slice-3/evidencia/revision_por_partes.md`): escapar saltos de línea en el registro de accesos (inyección de líneas); que `pap servir` avise que está listo después de abrir el puerto; la altitud por distrito del SIEN (H-G).

## Slice 5 — Ola 1 (esbozo)

- Primero GA-13 y X-06. Luego un tema por sub-slice, empezando por el que más preguntas reales tenga en la beta.
