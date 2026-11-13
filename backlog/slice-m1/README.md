# Slice M1 — Planificador (spike), índice enriquecido y fichas

- **Rama:** `slice-m1`, desde `main` (`f76b7eb` o posterior; la etiqueta `slice-m0-cerrado` está en `0ac8c7b`).
- **Fase 1** del diseño. Plan general: `../plan_slices.md`.
- **Escrito por el supervisor el 12/11/2026,** con lo medido en M0, la auditoría del supervisor del cierre de M0 y las respuestas del dueño de ese día. Lo validaron dos subagentes (uno como implementador contra el repo y otro de coherencia con el diseño); se corrigieron sus hallazgos.

## Documentos de referencia (leer antes de empezar)

1. `docs/diseno/motor_inferencia.md`: §4, §7 a §21, §23, §24, §26 y los anexos A y B.
2. `docs/diseno/fichas.md` (nuevo): fichas de tabla, bloques y temas provisionales.
3. `docs/diseno/tecnologias.md`: §6 a §8b.
4. `backlog/slice-m0/evidencia/cierre.md` y `revision_por_partes.md` (sección «Para M1 o después»).
5. `agents.md`.

## Objetivo

Que el motor responda **a la sombra** preguntas nuevas sobre la ENDES 2024 (tablas de niño, mujer y hogar): elige el dato, pregunta cuando duda o dice «no puedo» con alternativas. Se mide con unas 100 preguntas. **La web sigue respondiendo con el motor actual.**

```
pregunta → intérprete (modo motor) → ¿receta? → recuperador (bloques y variables) → planificador (3 muestras, elige por ID)
        → verificador → huellas u,y → decisión 1 → ejecutor → compuertas → decisión 2 → contraste y sello → respuesta v2 (sombra)
```

Para eso hacen falta antes cuatro cosas que M0 no tenía: la clase de cada variable (hoy vacía en casi todo el índice), el índice enriquecido (qué pregunta cada variable y a quién), las fichas y bloques, y el diseño muestral de todas las tablas de niño, mujer y hogar.

## Decisiones del dueño del 12/11/2026 (las aplica M1-01)

| Consulta | Decisión |
|---|---|
| K-03 | **Visto** a las tablas curadas de M0-06 y a las 3 recetas: pasan a `verificado` |
| K-01 | Lista de descargas **revisada**. Se amplía (fichas §4) y se agregan los documentos n.º 8, 9 y 11 del listado del INEI, y el informe de programas presupuestales de 2024 que ya está en la bandeja (fuente de las doradas) |
| C-M0-06-1 | 2024–2025 pasa a `conglomerados_repetidos` (HV001). Cita: ficha técnica de la ENDES 2025, §3.1 y §IV. Se aprueba registrar esa ficha |
| C-M0-06-2 | Tramos de edad del INEI. Anemia: 6–8, 9–11, 12–17, 18–23 y 24–35 meses. Desnutrición crónica: menores de 36 y 36–59 meses. No se ofrecen tramos más finos |
| C-M0-06-3 | «Costa» = «Lima metropolitana» + «Resto Costa» de SHREGION, con la nota «verificado contra las cifras publicadas». La categoría 1 se rotula «Lima Metropolitana y Callao» |
| C-M0-06-4 | HV270 (y V190) se aceptan con el rótulo del INEI, «quintil de bienestar». La duda sobre la versión queda como nota |
| C-M0-05-2 | Las 341 filas de REC93DVdisciplina sin la mujer en REC0111 se **excluyen de todo cálculo** de disciplina infantil, con nota y prueba |
| C-M0-11-1 | Tope de F-04 para la ENDES 2015–2025: **2 GB en el Mac y 1,5 GB en el repo privado**; si un bloque lo pasa, se detiene y se consulta |
| C-M0-11-2 | Los límites de precisión (R-ENC-03 y R-ENC-04) **se aplican también con 25 a 49 casos** |
| K-07 | Regla de no respuesta del ítem (R-ENC-19): aviso si pasa de 5 % y «aproximada» si pasa de 20 %, como valores iniciales |
| K-05 | Tope del LLM: **US$ 5 por día** y **US$ 20 por lote** de enriquecimiento |
| K-04 | 3 horas por semana del dueño para revisiones. **No es una restricción** para avanzar: lo que espera un visto queda en `propuesto` o `revisado` y el trabajo sigue |
| K-08 | Parquet de la ENAHO: se publican año por año, solo si la ficha de ese año en la Plataforma Nacional de Datos Abiertos declara ODbL; si no, van al repo privado. El catálogo pasa INEI-ENAHO a `ODbL-1.0` |
| D-M0-10-1, D-M0-03-1, D-M0-05-1 | Aceptadas. D-M0-10-1 se corrige en M1-03 |
| Liberar los ZIP de 2024 | No por ahora |
| Varias fuentes (10/11/2026) | El proyecto va por los niveles 1 (cada fuente responde su parte) y 2 (cruce por territorio común). En M1 solo se prepara: bloques (M1-06) y contrato con partes por fuente (M1-16) |

## Historias

Orden: las etapas A y B pueden avanzar en paralelo; la etapa C depende de ambas. (En este slice, «bloque» a secas es el **bloque temático** de `fichas.md`; no es `curados/motor/textos/bloques.yaml` ni el bloque de respaldo `endes-2024`.)

| ID | Historia | Depende de | Estado |
|---|---|---|---|
| **Etapa A. Base** | | | |
| M1-00 | [Preparación, descargas y auditoría de dependencias](M1-00-preparacion.md) | — | hecha ([documentos](evidencia/m1-00_documentos.md), [respaldo](evidencia/m1-00_respaldo.txt), [modelos](evidencia/auditoria_modelos_lista_dueno.md), [fuentes](evidencia/m1-00_modelos_fuente.md), [semilla](evidencia/m1-00_semilla.md)); cubo sigue en `010ea965` |
| M1-01 | [Decisiones del 12/11, reglas y tablas curadas](M1-01-decisiones.md) | M1-00 | hecha ([cambios de estado](evidencia/m1-01_cambios_de_estado.md), [catálogo](evidencia/m1-01_catalogo.md)) |
| M1-02 | [Deuda de M0 que conviene pagar antes de crecer](M1-02-deuda-m0.md) | M1-00 | hecha ([deuda](evidencia/m1-02_deuda.md), [pool Mac](evidencia/m1-02_pool_mac.txt), [pool Linux](evidencia/m1-02_pool_linux.txt)); consultas C-M1-02-1 a 3 |
| M1-03 | [Uniones entre tablas hermanas, universo por medición y cortes nuevos](M1-03-uniones-universo.md) | M1-00; M1-01 para los valores decididos | hecha ([evidencia](evidencia/m1-03.md), [doradas](evidencia/m1-03_doradas_cortes.md), [revisión](evidencia/m1-03_revision.md): aprobado con observaciones) |
| **Etapa B. Índice y fichas** | | | |
| M1-04 | [Texto de los cuestionarios y vínculo con las variables](M1-04-cuestionarios.md) | M1-00 | en curso: C-M1-04-1 resuelta (13/11); lote de prueba en vivo (RECH6, REC43, REC0111) corrido y borrado, US$ 1,14; 76 % de respuestas en prosa: falta activar la salida estructurada ([lote](evidencia/m1-04_lote.md)). Extracción corregida (sección 10 en pp. 72–81, anexo del carné y calendario), medición y lote con proveedor falso hechos ([cuestionarios](evidencia/m1-04_cuestionarios.md), [vínculos](evidencia/m1-04_vinculos.md), [lote](evidencia/m1-04_lote.md)) |
| M1-05 | [Enriquecimiento del índice](M1-05-enriquecimiento.md) | M1-01, M1-04 | tarea 0 hecha ([clases](evidencia/m1-05_clases.md)); el resto espera el lote en vivo de M1-04 (C-M1-04-1) |
| M1-06 | [Fichas de tabla, bloques y temas](M1-06-fichas-bloques.md) | M1-04; M1-05 (tarea 0) | hecha ([evidencia](evidencia/m1-06.md), [revisión](evidencia/m1-06_revision.md): aprobado con observaciones); lote en `propuesto` para el visto del dueño; C-M1-06-1 |
| M1-07 | [Diseño muestral y universos de niño, mujer y hogar; lote a `revisado`](M1-07-diseno-lote.md) | M1-05, M1-06 | pendiente |
| **Etapa C. Motor** | | | |
| M1-08 | [Intérprete en modo motor](M1-08-interprete.md) | M1-05 (sinónimos y cortes) | pendiente |
| M1-09 | [Recuperador](M1-09-recuperador.md) | M1-05, M1-06; modelo bajado por el dueño | pendiente |
| M1-09b | [Banco de pruebas del recuperador](M1-09b-banco-recuperador.md) | M1-09; conjunto semilla (M1-00); modelos bajados por el dueño | pendiente |
| M1-10 | [Planificador](M1-10-planificador.md) | M1-09 | pendiente |
| M1-11 | [Verificador completo, huellas y decisión 1](M1-11-verificador-decision.md) | M1-03, M1-07, M1-10 | pendiente |
| M1-12 | [Aclaraciones](M1-12-aclaraciones.md) | M1-11 | pendiente |
| M1-13 | [Sustitución y alternativas](M1-13-sustitucion.md) | M1-11 | pendiente |
| M1-14 | [Comparaciones entre grupos](M1-14-comparaciones.md) | M1-11 | pendiente |
| M1-15 | [Contraste, sellos y confianza](M1-15-sellos.md) | M1-11 | pendiente |
| M1-16 | [Contrato v2 y respuesta](M1-16-contrato-respuesta.md) | M1-12 a M1-15 | pendiente |
| M1-17 | [Caché, costo y concurrencia](M1-17-cache-costo.md) | M1-16 | pendiente |
| M1-18 | [Modo sombra](M1-18-sombra.md) | M1-16 | pendiente |
| M1-19 | [Conjunto de evaluación y medición](M1-19-evaluacion.md) | M1-18; preguntas del dueño | pendiente |
| M1-20 | [Revisión independiente y cierre](M1-20-cierre.md) | todas | pendiente |

## Lote de tablas de M1

- **Hogar:** RECH0, RECH23, RECH1, RECH4.
- **Niño:** RECH6, REC21, REC41, REC43, REC44, REC94, REC95, DIT.
- **Mujer:** REC0111, REC91, RE223132, REC42, RE516171, RE758081, RECH5.

Las demás tablas tienen ficha (M1-06), pero no entran al planificador en M1.

## Del dueño (no bloquea empezar)

1. **Bajar tres modelos** de Hugging Face y dejarlos en `biblioteca/cruda/bandeja/`, en la carpeta de cada modelo, con los archivos y el commit exactos que entrega el agente con las auditorías (ONNX, `tokenizer.json` y los JSON de configuración):
   - `intfloat/multilingual-e5-small` (se necesita en M1-09);
   - `ibm-granite/granite-embedding-97m-multilingual-r2` (M1-09b);
   - `ibm-granite/granite-embedding-311m-multilingual-r2` (M1-09b).

   Si falta alguno, el banco de M1-09b corre con los que haya.
2. **Escribir de 40 a 60 preguntas** del conjunto de evaluación (M1-19, tarea 2). Puede hacerlo desde ya.
3. **Vistos por lote:** tablas curadas nuevas (M1-07), fichas y bloques (M1-06) e índice (M1-07). Mientras no lleguen, el agente sigue con lo que no depende de ellos.
4. **Aprobar** la lista de cambios de estado por las compuertas nuevas (M1-01), `no_cubre.yaml` (M1-05) y los textos de las aclaraciones (M1-12).
5. **Anotar el universo** de cada plan esperado del conjunto de evaluación, junto con el auditor-agente (M1-19).

## Reglas del slice

- **Ninguna historia cambia una cifra del cubo `010ea965` ni de las recetas.** La única excepción prevista es el **estado** de publicación por C-M0-11-2 (M1-01), que se mide y se informa antes de aplicar.
- **Nada cambia en lo que responde la web,** con la misma excepción del estado por C-M0-11-2. Ningún tema pasa a `motor.version: nuevo`; el motor nuevo corre a la sombra (M1-18).
- **El LLM elige por ID y no produce números** (P-01). Ningún camino nuevo ejecuta SQL fuera de `ejecutar_select`.
- **Toda dependencia o modelo nuevo entra con su auditoría** (`plantillas/auditoria_dependencia.md`).
- **No se hace commit mientras el dueño u otro proceso edita archivos versionados.**
- Cada historia cierra con su evidencia en `evidencia/` y la suite en verde. Las consultas van a `consultas_al_dueno.md` de este slice.

## Definición de hecho

1. Las métricas del §23.3 del diseño están informadas con su intervalo de Wilson, en total y por estrato.
2. El p95 por etapa está medido en el Mac y comparado con el §21.
3. El número de muestras y el esfuerzo del planificador están decididos con datos.
4. El modo sombra corre sin errores sobre Q1–Q4, la matriz y el conjunto de evaluación.
5. Las 90 filas de 2024 siguen iguales al cubo; las doradas nuevas por región natural, quintil y tramo de edad se reproducen (±0,1 pp).
6. `pap fichas validar`, `pap inferencia validar-tablas` y `validar-recetas` salen con 0.
7. Suite completa en verde, gitleaks en 0, `pip-audit` en verde y auditorías de dependencias aprobadas.

## Fuera de M1

Otros años de la ENDES (M2), la ENAHO (M3), cambiar lo que ve el usuario (M4), el orquestador de varias fuentes y el cruce de nivel 2 (después de M3), y el frente de datos en paralelo (backlog aparte).
