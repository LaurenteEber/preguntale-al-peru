# Verificación independiente de la adenda del slice 1 (S1-16)

Informe del verificador independiente (subagente nuevo, distinto del implementador; P-06), con el encargo de `encargo_verificador.md`. Se transcribe tal como lo entregó. La corrección de sus hallazgos y la segunda verificación, limitada a ellos, están al final («Corrección y segunda verificación»).

---

## Primera verificación

Verificador: subagente nuevo, distinto del implementador (P-06). Rama `slice-1-adenda`, base `0166c59`. Empecé con HEAD en `614f7d1`. Mientras verificaba entraron dos commits: `f2fa4ef` (solo documentación) y `5206221` (cambia `tests/matriz/comprobar.py`, ver A-1). Ninguno de los dos toca `src/` ni `curados/`, así que todas las respuestas del motor que leí siguen valiendo para el HEAD actual. No edité ningún archivo del repositorio. Las salidas están en `salidas/verificador/`, `salidas/matriz_verificador/` y en un directorio temporal fuera del repositorio.

### Veredicto: **no apto**

Casi todo se cumple, y lo comprobé por mi cuenta:
- el cubo nuevo solo agrega las filas en soles constantes;
- el factor del IPC coincide con mi cálculo a mano;
- Q1–Q4 no cambian sus cifras;
- las reglas se regeneran sin cambios;
- las pruebas pasan sin fallos.

**El punto 5 de la definición de hecho no se cumple.** La matriz completa da 11 casos con fallo. Los 11 son evoluciones de gasto en las que la cifra del año de comparación (2023) se suprime. En esos casos la respuesta:
- no compara nada;
- muestra una sola cifra en soles de 2025;
- dice «para que se puedan comparar entre años»;
- no dice primero que la comparación no se puede hacer.

Después de que aparecieron esos fallos, el commit `5206221` relajó la comprobación de la matriz en lugar de corregir la respuesta (A-1).

### Tabla por punto de la definición de hecho

| Punto | Estado | Evidencia |
|---|---|---|
| 1. Biblioteca | **cumple** | `git show 0166c59:…/manifiesto_p1_indicadores.json` registra `fact_indicador` con `sha256:ba1fbc55eb68…`, 39 539 filas. `sha256sum biblioteca/_respaldo_pre_adenda/indicadores/fact_indicador.parquet` da `ba1fbc55eb689141…ba8`. El cubo actual da `010ea965…66f` con 48 319 filas, lo mismo que dice el manifiesto en HEAD. Comparación propia con DuckDB, sobre todas las columnas salvo `version_tabla`: `viejo EXCEPT ALL nuevo` = **0 filas**. `nuevo EXCEPT ALL viejo` = 4 397 filas `gasto_ex_pan/devengado_constante` y 4 383 `gasto_ex_pan_opcion_c/devengado_constante`, y nada más. `anio_base_deflactor` es BIGINT y `factor_deflactor` es DOUBLE; ambas son no nulas en las 8 780 filas constantes y nulas en todas las demás (0 excepciones). `version_tabla` = `1.2.0` en las 48 319 filas (antes `1.1.0`). `git diff 0166c59..HEAD --stat -- biblioteca/cruda curados/insumos.lock.yaml` sale vacío. Las 32 tablas de `dimensiones/` del respaldo tienen la misma huella que las actuales; `dim_ipc` es `2d33b25a…` |
| 2. Soles constantes | **cumple con observación** | El factor a mano coincide (sección siguiente). Las 8 780 filas cumplen `valor = devengado × factor`: diferencia máxima 2,4·10⁻⁷ soles, ninguna fila constante sin su par. Montos nominales nacionales sin cambio: 2 179 204 677,87 / 2 429 016 663,42 / 2 455 856 886,10, igual que el respaldo (G-07: 2 179 / 2 429 / 2 456 millones). El año base no está escrito a mano: `calculo.py:395-399` toma el mayor año con IPC completo y con gasto; `respuesta.py` lo lee del cubo. El validador usa `ctx.anio_actual - 1` (`reglas_etapa1_3.py:1068`, con `anio_actual=2026` en `nucleo.py:123`). Los dos dan 2025. `pap preguntar --intencion evolucion --tema gasto_publico --territorio "Perú"` responde: «pasó de S/ 2 263,9 millones en 2023 a S/ 2 455,9 millones en 2025, en soles de 2025: aumentó». No da diferencia ni porcentaje. «Ojo al leer» trae el mensaje de R-GASTO-12. R-GASTO-12 queda en `rotular · soles_constantes`, `bloqueos_cruce` vacío y `accion_final` = `publicar`. «Para citar» da el monto registrado de cada año y el factor (1,0388706 y 1,0000000). `nivel_actual` sigue en soles corrientes, con el mismo texto que la base (diferencial con la base: idéntico salvo la huella). Observaciones: B-1 y M-1 |
| 3. Hallazgos de la revisión | **cumple con observación** | **H11/AD-1:** `evolucion anemia Perú` trae en «Más contexto» la tarjeta «2024 y 2025, con la forma de medir actual» (35,3 % y 34,9 %), el marcador `{{c:endes_anemia_6_35m_oms2024__…__2024__contexto}}` y su línea en «Para citar». **N-2/A-H6:** `--hasta 2024` responde con la forma anterior 2015–2024 (43,4 % → 43,7 %, sin cambio claro). Muestra la vigente de 2024 (35,3 %) con su marcador y su cita, y el «Ojo» dice «Con la forma de medir actual solo hay datos desde 2024». No aparece «más reciente». En la base esta consulta era «no se puede». `--hasta 2018` responde 2015–2018. `--hasta 2010` y `--desde 2025` siguen en «no se puede». **H9:** ninguna capa 1 de `cruce` contiene «lado a lado» (Puno departamento, Lima Metropolitana, Lima Región, Callao, Perú); en la base sí aparecía. `git diff … comunes.yaml` sale vacío. **H12/AD-2:** la frase exacta está en el `mensaje_usuario` de R-CRUCES-07 y en `frases_estandar.efecto`, y la primera oración de cada uno no cambió. `git diff … reglas/propuestas` sale vacío. Volví a correr el consolidador: la huella de `reglas.json` sigue en `0682897f…` y `git status` no cambió. El diff de `reglas.json` contra la base solo toca R-TERRITORIO-09, R-CRUCES-07 y `frases_estandar.efecto`. vp3: `cierres_abiertos: []`. Guardia: `fallos: 0`. `validar-reglas`: 535/535. Q3 no se contradice («cómo está el indicador» junto a «no podemos mostrar cómo cambió»), y el 5 % dice «del gasto atribuido al departamento de Lima», que coincide con el denominador de `calculo.py:303-315`. **D-01:** «Lima» ofrece 1) Lima Metropolitana, 2) Lima Región, 3) Callao, y `ambiguos_conocidos` en `reglas.json` va en ese orden. **N-3:** el «No permite concluir» dice «Lima Metropolitana y Lima Región»; en la base solo nombraba Lima Metropolitana. **H7:** `--anio 2018` sigue en «no se puede»: «…La cifra de 2018 solo existe con la forma de medir anterior…», y ofrece «Puedes preguntar cómo cambió la anemia en Perú hasta 2018», consulta que sí responde. `--anio 2010` da «No hay datos de anemia de 2010.», sin «forma de medir actual». Observación: B-2 |
| 4. Regresión Q1–Q4 | **cumple** | `uv run pytest -q tests/test_regresion_q1_q4.py`: 9 pasan. Leí la prueba: compara de forma exacta los `CAMPOS_CIFRA` (sin `version_tabla`), el semáforo de la respuesta, el nivel de confianza, `respuesta_parcial`, las comparaciones bloqueadas, las reglas firmes y `accion_final`; también el límite de palabras, el corrector y la ausencia de marcadores. Toda diferencia de texto tiene que estar aprobada. `Q1.yaml`: la cita de 2024 y la tarjeta AD-1 llevan `aprobado_por: dueño` con su motivo (AD-1, fila R-04). `Q3.yaml`: la frase AD-2 lleva `aprobado_por: dueño` (fila R-03). El cambio del 5 % lleva `aprobado_por: agente`; según mi propio juicio cumple §5.1: misma cifra, hace explícito el denominador que el cálculo ya usa, sin afirmación nueva y la capa 1 no cambia. `Q2.yaml`, `Q4.yaml` y `tests/referencias/` no cambiaron. Observaciones de trazabilidad en B-3 |
| 5. Pruebas y matriz | **no cumple** | `uv run pytest -q -m "not solo_mac" -p no:cacheprovider`: **741 pasan, 34 excluidas, 0 fallos** (la base de la nube registraba 714 y 34). Con HEAD `5206221`, `tests/test_matriz_cobertura.py` da 22 pasan. **Matriz:** `backlog/slice-1/evidencia/adenda/matriz.md` (sin commit, generado con `f2fa4ef`) dice «Casos: 5086 · con fallos: 11», con 0 errores. Mi corrida propia (`salidas/matriz_verificador`) da lo mismo: 5 086 casos, 0 errores, **11 fallos `evolucion_sin_las_dos_cifras`**, todos de `gasto_publico`: Antonio Raymondi, Caravelí, Elías Soplín Vargas (×2), Kumpirushiato (×3), Mollebaya, Capachica y San Juan (opción 1, ×2). Ver B-1 y A-1 |
| 6. Cambios sin historia | **cumple** (con la observación A-1) | `git diff 0166c59..HEAD --stat -- curados/capa0 tests/fixtures docs/decisiones.md reglas/propuestas tests/referencias` sale vacío. Revisé las pruebas existentes que cambiaron (`test_cli_preguntar`, `test_no_se_puede`, `test_planificador`, `test_regresion_q1_q4`, `test_respuesta_p3`, `test_s1_09_correcciones`): cada cambio cita AD-1, AD-2 o H7 y corresponde a un comportamiento pedido, no a tapar un fallo. La excepción está fuera de esas rutas: `tests/matriz/comprobar.py` en `5206221` (A-1) |

### Cálculo a mano del factor del IPC (desde `biblioteca/dimensiones/dim_ipc.parquet`)

Serie PN38705PM, base dic. 2021 = 100. 2023 y 2025 tienen `anio_completo = true` y 12 meses con dato. 2026 tiene 8 meses y no es año cerrado.

- **2023:** suma de los 12 índices mensuales (108,704764 … 111,970400) = 1 332,589358, así que el promedio es 1 332,589358 / 12 = **111,049113**. Coincide con `ipc_prom_anual` = 111,049113.
- **2025:** suma (114,065534 … 115,894705) = 1 384,387863, así que el promedio es 1 384,387863 / 12 = **115,365655**. Coincide con `ipc_prom_anual` = 115,365655.
- **Factor 2023→2025** = 115,365655 / 111,049113 = **1,03887057**. Con los valores de `ipc_prom_anual` sin redondear da 1,0388705671156508, idéntico al `factor_deflactor` del cubo para 2023. Con los índices mensuales redondeados a 6 decimales da 1,0388705678 (diferencia de 7·10⁻¹⁰).
- Control 2024: 115,365655 / 113,659538 = 1,0150108, igual al cubo. 2025: 1,0.
- Control nacional: 2 179 204 677,87 × 1,0388705671 = 2 263 911 599,56, igual a la fila `devengado_constante` de 2023.

### Hallazgos

| ID | Severidad | Qué pasa | Evidencia |
|---|---|---|---|
| B-1 | **bloqueante** (incumple el punto 5) | Cuando la cifra del año de comparación (2023) se suprime por precisión, la evolución del gasto no dice primero que no se puede comparar. Responde «Esto es lo que dicen los datos oficiales…» con una sola cifra en soles de 2025, y el «Ojo al leer» dice «Montos en soles de 2025 (ajustados por inflación), para que se puedan comparar entre años», aunque no compara nada. En el caso «intermedio» la cifra clave es **S/ 76 mil**, con «Fuente: gasto registrado en el MEF 2024», pero lo registrado fue S/ 75 mil (74 815). Es decir, se muestra deflactada una cifra de un solo año, al revés de «una cifra de un solo año sigue en soles corrientes». Una opción: si el año de comparación no se puede publicar, comparar con el año publicable más cercano, o dar «no se puede comparar» primero y la cifra del año en soles corrientes | `pap preguntar --intencion evolucion --tema gasto_publico --territorio "Kumpirushiato, La Convención"`: el plan trae la cifra `…__2023__contexto`, pero la respuesta no la usa. `nivel_actual … --anio 2023` da «no es lo bastante precisa». Caso intermedio: `salidas/matriz_verificador/respuestas/0026.md`. Los 11 casos de la matriz son todos este patrón |
| A-1 | **alto** | El commit `5206221` (20:23, después de que la matriz mostró los 11 fallos) cambia `tests/matriz/comprobar.py::evolucion`. Ahora la comprobación se salta el caso si el año de comparación no aparece en el texto visible. Con eso los 11 casos de B-1 pasan sin que haya cambiado nada en la respuesta. La regla de que el agente no ajusta una prueba para que pase se aplica aquí en su espíritu, aunque no sea una dorada. El texto sí «promete» la comparación («para que se puedan comparar entre años»). Hay que corregir el motor, o que el dueño decida que esa respuesta es aceptable | `git show 5206221` |
| M-1 | medio | En una evolución de gasto cuyo año principal no es el año base (p. ej. `--hasta 2024`), el recuadro de la cifra clave dice «S/ 2 465,5 millones … en 2024. Fuente: gasto registrado en el MEF 2024» sin el rótulo «en soles de 2025», cuando el MEF registró S/ 2 429,0 millones (G-07). La respuesta corta y el «Ojo» sí lo rotulan, pero el recuadro suelto se puede citar mal | `salidas/verificador/gasto_h2024/` |
| B-2 | bajo | «Con la forma de medir actual solo hay datos desde 2024» y «La cifra de 2018 solo existe con la forma de medir anterior» chocan con el bloque «Por qué hay dos formas de medir»: «…aunque el INEI también publicó años anteriores con ella». E-06 respalda la frase («la forma vigente solo tiene 2024–2025»), así que no es una infracción. Una opción: «solo tenemos datos desde 2024» | `anemia_h2024`, `h7_2018`, `anemia_evol` |
| B-3 | bajo | Trazabilidad de aprobaciones: en `Q3.yaml` la entrada de la frase AD-2 pasó a `aprobado_por: dueño` aunque también incluye el «Lima, Lima» que antes había aprobado el agente (el motivo lo dice). En `Q1.yaml` se reutilizó la entrada C-01 del dueño para la cita AD-1. Es correcto en el fondo, pero mezcla quién aprobó qué. La regresión excluye la nueva cifra AD-1 de la comparación de reglas porque no tiene referencia | `git diff 0166c59..HEAD -- backlog/slice-1/evidencia/regresion/` |
| B-4 | bajo | El año base se deduce por dos caminos distintos: de los datos en `calculo.py` y como `ctx.anio_actual - 1` en el validador. Hoy los dos dan 2025. Si se separan (p. ej. en 2027 sin el IPC de 2026), el validador bloquea, lo que es seguro, pero conviene tener una prueba que los ate | `calculo.py:395`, `reglas_etapa1_3.py:1068` |

**Observaciones que ya estaban en la base (no cuentan como hallazgos de la adenda):**
- capa 1 de `cruce` con «Esto es lo que se gastó :» (espacio antes de los dos puntos) en Lima Metropolitana, Lima Región, Callao y Perú;
- «El 6 % del gasto del departamento…» en la ficha de una cifra nacional;
- `--hasta 2010` dice «solo permiten una cifra» cuando no hay ninguna;
- la evolución de `gasto_ex_pan_opcion_c` dice «no tenemos dos años» aunque hay datos de 2023–2025;
- la cita de 2018 apunta a una tabla «Principales indicadores 2019-2024, columna 2018» (dorada curada);
- «Eso no quiere decir que no haya casos» en una respuesta de gasto (Ayaviri);
- la cita de 2024 de la forma vigente lleva un intervalo propio con «Fuente: INEI»;
- R-TERRITORIO-09 conserva en `decisiones_dueno_2026_10_09` el texto histórico de L4 con cuatro opciones.

Comprobé cada una con la misma consulta corrida sobre `0166c59` y el cubo del respaldo.

### Pruebas y comandos corridos

| Comando | Resultado |
|---|---|
| `uv run pytest -q -m "not solo_mac" -p no:cacheprovider` (HEAD `614f7d1`) | 741 pasan, 34 excluidas, 0 fallos (4 min 13 s) |
| `uv run pytest -q tests/test_regresion_q1_q4.py` | 9 pasan |
| `uv run pytest -q tests/test_matriz_cobertura.py` (HEAD `5206221`) | 22 pasan |
| `uv run python tests/matriz/correr.py --salida salidas/matriz_verificador` | 5 086 casos, 0 errores, **11 fallos**, salida 1 |
| `python3 reglas/consolidador/consolida_reglas.py` | salida 0; `reglas.json` sigue en `0682897f…`; `git status` sin cambios |
| `python3 -I reglas/consolidador/pruebas/vp3_checks.py .` | salida 0, `cierres_abiertos: []` |
| `python3 reglas/consolidador/pruebas/prueba_guardia.py` | `fallos: 0` |
| `uv run pap validar-reglas` | 535/535; 68 reglas implementadas de 68 |
| Comparación propia del cubo con DuckDB (respaldo contra actual) | 0 filas viejas cambiadas; solo 8 780 filas nuevas `devengado_constante` |
| `pap preguntar` (evolución de gasto: Perú, Lima Metropolitana, Ayaviri, `--desde 2024`, `--hasta 2024`, opción C, Kumpirushiato; nivel_actual de gasto; evolución de anemia: Perú, `--hasta 2024/2018/2010`, `--desde 2025`; cruce: Puno, Lima Metropolitana, Lima Región, Callao, Perú; «Lima»; comparación Lima Metropolitana / Lima Región; anemia `--anio 2018/2024/2010`; `curados/motor/consultas_minimas/`) | Resultados descritos arriba |
| Las mismas consultas sobre una copia de `0166c59` (vía `git archive`) con el cubo del respaldo | Diferencial: `nivel_actual` de gasto idéntico; los cambios observados son los esperados de cada historia |

---

## Corrección y segunda verificación

(pendiente)
