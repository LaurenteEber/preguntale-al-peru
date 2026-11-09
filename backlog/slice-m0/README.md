# Slice M0 — Cimientos del motor de inferencia

- **Rama:** `slice-m0`, desde `main` en `slice-3-cerrado` (`2a8f18d` o posterior).
- **Fase 0** del diseño. Plan general: `../plan_slices.md`.
- **Validación:** el backlog lo revisaron, el 9/11/2026, un subagente que emuló al implementador contra el repo y otro de coherencia con el diseño. Se corrigieron sus 45 hallazgos.

## Documentos de referencia (leer antes de empezar)

1. `docs/diseno/motor_inferencia.md`:
   - §1–7, §8.1, §11.2, §11.3, §12.1, §14, §15, §22, §23.1, §26 y §27;
   - los anexos A y B.
2. `docs/diseno/tecnologias.md`: §1–5 y §9.
3. `agents.md` (lo actualiza M0-01).

## Objetivo

Que el proyecto **calcule desde los microdatos de la ENDES 2024** con la arquitectura del motor nuevo, y que esas cifras **igualen al cubo actual**. Nada cambia para el usuario: la web sigue con el motor actual.

```
ZIP de la ENDES 2024 (registrados uno por uno y respaldados en el repo privado de crudos)
  → pap microdatos convertir   → biblioteca/microdatos/ENDES/2024/*.parquet + manifiesto (+ huellas en insumos.lock.yaml)
  → pap variables indexar      → biblioteca/variables/{archivos,variables,categorias}.parquet
  → curados/inferencia/*.csv|yaml (diseño muestral, universos, territorios, perfil, relación, cortes)
  → receta (YAML) → gramática → verificador (diseño y universo derivados) → ejecutor (pool, svy) → compuertas
  → comparación con las 90 filas de 2024 del cubo 010ea965
```

## Cómo empezar (agente)

1. Leer este README, `agents.md` y los documentos de referencia.
2. **M0-00:** crear la rama `slice-m0`, hacer el primer commit con los documentos nuevos y guardar la base.
3. **M0-00b:** corregir la seguridad del repo actual, en un commit propio y con la regresión sin cambios.
4. **En paralelo, con lo que no espera al dueño:** M0-01, y después M0-03.
5. **M0-02** espera K-06 y K-01. Mientras tanto se avanzan las partes de M0-04 a M0-08 que se prueban con datos sintéticos, y se marca qué queda pendiente del dato real.
6. Cada historia cierra con su evidencia en `evidencia/` y la suite en verde. Las consultas van a `consultas_al_dueno.md`.

## Antes de empezar

0. **Los documentos nuevos están en el árbol de trabajo del Mac, sin commit:**
   - `docs/diseno/motor_inferencia.md` y `docs/diseno/tecnologias.md`;
   - `backlog/README.md` (una línea sobre los slices del motor) y `backlog/plan_slices.md` (reemplazado);
   - `backlog/slice-m0/` y `backlog/slice-m1/README.md`.

   **El primer commit de la rama `slice-m0` los agrega** (M0-00, tarea 1).
1. **Del dueño, sin bloquear el inicio:** K-09 (token de `gh` y Push protection). Se necesita en M0-02, tarea 5.
2. **Del dueño, antes de M0-02:**
   - responder K-06 (formato de la serie);
   - aprobar la lista de ZIP (K-01).
3. **Del dueño, antes de cerrar M0-09:** confirmar R en el Mac (K-02).
4. **Repo privado de crudos:** `git@github.com:LaurenteEber/preguntale-al-peru-crudos.git`, creado por el dueño el 9/11/2026. Falta el token de `gh` de grano fino (K-09).
5. **Nada de esto cambia lo que responde la web.** M0-00b solo toca dependencias, la imagen y la lectura segura de los ZIP. Q1–Q4, la matriz y la evaluación grabada no cambian en ninguna historia.

## Historias

| ID | Historia | Depende de | Estado |
|---|---|---|---|
| M0-00 | [Preparación](M0-00-preparacion.md) | — | hecha ([evidencia](evidencia/m0-00_interfaces.md)) |
| M0-00b | [Seguridad: correcciones del repo actual y controles](M0-00b-auditoria-seguridad.md) 
| M0-01 | [Decisiones, reglas y `agents.md`](M0-01-decisiones-reglas-agents.md) | M0-00 | hecha ([evidencia](evidencia/m0-01_decisiones.md)); R-ENC-19 espera K-07 |
| M0-02 | [ZIP de la ENDES 2024: lista, registro y respaldo](M0-02-zip-endes-2024.md) | M0-01; K-06 y K-01 | en curso: lista, descarga, registro y tamaños hechos ([evidencia](evidencia/m0-02_tamano_zip.md)); respaldo y restauración esperan K-09 |
| M0-03 | [Versiones: `svy` 0.35.0 y `pyreadstat` 1.3.7](M0-03-versiones.md) | M0-00b | hecha: cubo idéntico `010ea965` ([regresión](evidencia/m0-03_regresion_svy.csv), [lock](evidencia/m0-03_lock.md)); la comparación con R cierra en M0-09 |
| M0-04 | [Conversor y almacén](M0-04-conversor-almacen.md) | M0-02 (tareas 1–4: ZIP registrados), M0-03 | hecha: 34 archivos de 2024 ([evidencia](evidencia/m0-04_tamano.md)) |
| M0-05 | [Índice de variables y controles](M0-05-indice-variables.md) | M0-04 | hecha: 34 archivos, 2 856 variables ([conteos](evidencia/m0-05_conteos.md)); notas D-M0-05-1 y C-M0-05-2, que no bloquean |
| M0-06 | [Tablas curadas de 2024](M0-06-tablas-curadas.md) | M0-05 | hecha: 6 tablas, conteos 9 959 / 19 511 / 20 290 iguales al cubo ([tablas](evidencia/m0-06_tablas.md), [revisión](evidencia/m0-06_revision.md)); visto del dueño (K-03) pendiente; C-M0-06-1 a 4 abiertas, no bloquean M0 |
| M0-07 | [Gramática, verificador base y DuckDB endurecido](M0-07-gramatica-verificador.md) | M0-05; M0-06 con las tablas validadas (el visto del dueño solo condiciona `verificado` en M0-10) | hecha: 3 planes completos, 9 959 / 9 959 / 19 511 ([evidencia](evidencia/m0-07_gramatica.md)) |
| M0-08 | [Ejecutor: pool y adaptador de `svy`](M0-08-ejecutor.md) | M0-07 | hecha en el Mac: equivalencia con dif 0, p95 medido ([ejecutor](evidencia/m0-08_ejecutor.md), [tiempos](evidencia/m0-08_tiempos.md)); falta correr el pool en Linux |
| M0-09 | [Compuertas y verificador en R](M0-09-compuertas-verificador-r.md) | M0-08 | hecha: compuertas y 90 filas iguales al oráculo ([compuertas](evidencia/m0-09_compuertas.md)); `svy` 0.35.0 = R `survey` 4.5 en los 50 dominios del sintético, máx. 1,3e-15 ([R](evidencia/m0-09_r.md)) |
| M0-10 | [Recetas 2024 que igualan al cubo](M0-10-recetas-2024.md) | M0-08 y las compuertas de M0-09 (los esperados de R no la bloquean) | hecha salvo `verificado`: 90 filas con 0 diferencias, 21 de 21 doradas ([recetas](evidencia/m0-10_recetas.md), [90 filas](evidencia/m0-10_recetas_vs_cubo.csv), [revisión](evidencia/m0-10_revision.md)); `verificado` espera el visto del dueño (K-03) |
| M0-11 | [Medición, espacio local, documentación y cierre](M0-11-medicion-cierre.md) | todas | pendiente |

**Pueden ir en paralelo:**
- M0-00b con M0-01 y M0-02;
- M0-03 con M0-01 y M0-02 (después de M0-00b);
- la parte de R de M0-09 con M0-10.

**Si una espera del dueño bloquea una historia,** se sigue con las que no dependen de ella (`agents.md` §4).

**En cada historia:**
- `uv run pytest -q` (en la nube: `-m "not solo_mac and not navegador and not regresion_microdatos"`);
- la regresión Q1–Q4;
- la matriz reducida;
- la evaluación con grabaciones del slice 2.

**Desde M0-04, en el Mac:** `uv run pytest -q -m regresion_microdatos`.

## Definición de hecho del slice

1. **Recetas que igualan al cubo.** Las recetas `endes_anemia_6_35m`, `endes_anemia_6_35m_oms2024` y `endes_dci_menores_5`, calculadas por el motor nuevo desde los microdatos, igualan las **90 filas de 2024 del cubo `010ea965`**: 30 por indicador (1 nacional, 2 de área urbana y rural, 24 departamentos sin el Callao, Lima Metropolitana, Lima Región y Callao).
   - Valor, ee, IC, CV y deff redondeados a 8 decimales con |dif| ≤ 1e-8.
   - n_muestra y gl idénticos.
   - El n efectivo igual a mín(n, n efectivo del cubo).
   - Sin redondear, contra `calculo._svy_niveles` con |dif| ≤ 1e-12.

   Si alguna fila no iguala, es una consulta tipo C con su diagnóstico. Nunca se ajusta un dato ni una tolerancia.
2. **Índice completo** de la ENDES 2024 (M0-05, tarea 6).
3. **Ejecutor:** coincide con R `survey` en el microdato sintético (1e-9 en est, ee e IC; gl y n exactos). Pasa las pruebas de seguridad, de tiempo máximo y de memoria.
4. **Compuertas:** R-ENC-02 a R-ENC-04 leídas de `reglas/reglas.json`. Dan el mismo estado que el validador actual (`reglas_etapa4.py`) en las 90 filas.
5. **Medición en el Mac:**
   - tamaño del almacén de 2024 (y la proyección del tope de F-04);
   - variables y textos distintos del índice;
   - p95 del ejecutor (1 año: 25 y 100 dominios; 2 y 4 años apilados).
6. **Decisiones, reglas y `agents.md`** actualizados; `reglas.json` regenerado con el consolidador.
7. **Regresión:** Q1–Q4, la matriz y la evaluación grabada sin cambios. Suite completa en verde.
8. **Revisión independiente por partes,** con su evidencia en `evidencia/`.
9. **Seguridad:** las correcciones A1–A9 del repo actual aplicadas (Pillow, `certifi`, ZIP, lock, `.env`, imagen, Python, release y prueba de secretos); toda dependencia que entra o cambia tiene su auditoría aprobada; `just auditar` y gitleaks en verde.
10. **Espacio local:** el bloque ENDES 2024 está `respaldado` en el repo privado, con la restauración probada; `pap almacen liberar` probado en modo simulación; tamaño de los ZIP y de los Parquet medido.

## Decisiones del dueño que afectan este slice

**8/11/2026:**
- Motor a pedido desde los microdatos, con el cubo y las doradas como regresión.
- `verificado` solo para las recetas que reproducen su cifra oficial. Lo demás llega a `revisado` con el auditor-agente y el visto del dueño por lote.
- Tres alternativas (R-LENGUAJE-05).
- Benjamini-Hochberg en las familias de comparaciones.
- Política de `svy`: cada versión es una historia con su regresión.
- La serie OMS 2024 hacia atrás, después del MVP.
- Medias y medianas desde M3.
- El slice 4 (beta) en pausa hasta M4.

**9/11/2026:**
- Respaldo de los crudos en el repo **privado** `preguntale-al-peru-crudos` (el principal es público), con ciclo por bloque y liberación del espacio local.
- Auditoría de seguridad de todo lo que entra (bibliotecas, modelos, paquetes de R y repos de terceros).
- X-24: la ENDES da el porcentaje y el total se calcula con la población proyectada del INEI, desde M2.

## Supuestos que el agente puede fijar (tipo B)

Se marcan con `supuesto: M0-xx` y se registran en `consultas_al_dueno.md`:
- nombres internos;
- el tamaño de los bloques de lectura;
- los hilos por trabajador;
- `max_tasks_per_child`;
- los textos internos de los errores.

**Son tipo C:**
- cualquier cambio de cifra, regla o umbral;
- una fila de las tablas curadas sin respaldo en la ficha técnica o en `definiciones_endes.yaml`;
- cualquier diferencia con el cubo.

## Fuera de este slice

- El LLM y el enriquecimiento del índice (M1).
- La búsqueda, el planificador, las aclaraciones y la respuesta v2 (M1).
- Otros años y la ENAHO (M2 y M3).
- La web.
- El «¿cuántos?» (M2).
