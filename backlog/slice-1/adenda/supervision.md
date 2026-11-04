# Adenda del slice 1 — Lista de verificación del supervisor

4/11/2026. La usa el chat supervisor (y el dueño) para aceptar o devolver cada entrega de S1-11 a S1-16. No reemplaza los criterios de cada historia: los comprueba desde fuera, con comandos propios.

**Cómo se trabaja ahora:** el agente implementa en Claude Code en la nube, sobre el repo de GitHub. El supervisor revisa la rama `slice-1-adenda` desde GitHub (clon en su contenedor); el Mac solo se actualiza con `git pull`.

Leyenda: ✅ se acepta · ⛔ se devuelve (se detiene la adenda si lo dice `agents.md` §4) · 🔎 se revisa a mano.

---

## 0. Antes de que el agente empiece

| # | Comprobación | Cómo | Resultado esperado |
|---|---|---|---|
| 0.1 | `1ee2e7c` (adenda actualizada) está en GitHub | `git ls-remote origin main` | El hash de `main` es `1ee2e7c` o posterior |
| 0.2 | La nube tiene la biblioteca | Ver «Entorno en la nube» (§7) | Decisión X-11 tomada y paquete publicado |
| 0.3 | El agente lee las reglas actualizadas | `agents.md` §8 ajustado a la nube (§7) | No dice «solo en el Mac del dueño» |

## 1. S1-11 — Repositorio y biblioteca

| # | Comprobación | Cómo | ✅ si… | ⛔ si… |
|---|---|---|---|---|
| 1.1 | La rama nace de `main` actual | `git merge-base origin/main origin/slice-1-adenda` | = `1ee2e7c` o posterior | Nace de otro commit |
| 1.2 | Huellas iguales a las de la migración | `s1-11_reconstruccion.txt` + correr `comparar_manifiestos.py` yo mismo | Código 0; `fact_indicador` = `sha256:ba1fbc55…` | Cualquier huella distinta → consulta C |
| 1.3 | Base de pruebas | `evidencia/adenda/pytest_base.txt` | 748 pasan, 0 fallos | Fallos sin anotar en `consultas_al_dueno.md`, o «arreglados» |
| 1.4 | Respaldo para comparar | `ls biblioteca/_respaldo_pre_adenda/`; `git status --ignored` | Existe y aparece solo como ignorado | Está en git |
| 1.5 | Nada intocable cambió | `git diff 1ee2e7c..origin/slice-1-adenda --stat -- curados/insumos.lock.yaml biblioteca/cruda` | Vacío | Cualquier cambio |
| 1.6 | Commit con ID | `git log --oneline` | `S1-11: …` | — |

## 2. S1-12 — Gasto en soles constantes

**Cifras de control** (calcularlas por mi cuenta desde `dim_ipc.parquet`, no copiarlas del agente):

| Dato | Valor esperado |
|---|---|
| IPC prom. 2023 / 2025 | 111,049113 / 115,365655 |
| Factor 2023→2025 | **1,0388706** (= 115,365655 / 111,049113) |
| Gasto 2023 nominal → en soles de 2025 | S/ 2 179,2 → **S/ 2 263,9 millones** |
| Nominales de control G-07 | 2 179 / 2 429 / 2 456 millones (sin cambio) |

| # | Comprobación | Cómo | ✅ si… |
|---|---|---|---|
| 2.1 | Filas nuevas, solo donde corresponde | DuckDB sobre `fact_indicador.parquet`: `medida = 'devengado_constante'` | Solo en `gasto_ex_pan` y `gasto_ex_pan_opcion_c`, en todos los niveles y líneas con `devengado`; nada en PIM ni PIA |
| 2.2 | Columnas y versión | Esquema del Parquet | `anio_base_deflactor` (entero) y `factor_deflactor` (doble), nulas en las demás filas; `VERSION_TABLA` = `1.2.0` |
| 2.3 | `valor` = devengado × factor | Mi propia consulta | Diferencia < 1e-6 en todas las filas |
| 2.4 | Filas viejas intactas | Mi propio diff contra `_respaldo_pre_adenda/` (no solo `s1-12_comparar.py`) | Iguales en todas las columnas salvo `version_tabla` |
| 2.5 | Año base calculado, no fijo | `grep -n "2025" src/pap/motor/calculo.py respuesta.py` + prueba del agente | Sin año escrito a mano; prueba de que coincide con el validador (`ctx.anio_actual - 1`) |
| 2.6 | IPC incompleto → error | Prueba del agente | Existe y falla con mensaje claro |
| 2.7 | Respuesta | `uv run pap preguntar --intencion evolucion --tema gasto_publico --territorio "Perú" --salida <tmp>` | «pasó de S/ 2 263,9 millones en 2023 a S/ … en 2025, en soles de 2025: aumentó/disminuyó»; **sin % ni diferencia**; «Ojo al leer» con el mensaje de R-GASTO-12; sin `bloquear_cruce` |
| 2.8 | La cita permite verificar | «Para citar y verificar» | Nominal de cada año (S/ 2 179,2 millones en 2023) y el factor |
| 2.9 | Una cifra de un solo año no cambia | `nivel_actual gasto_publico Perú` antes/después | `respuesta.json` idéntico salvo versión de tabla |
| 2.10 | Q3 sin cambios de cifras | Regresión | Igual |
| 2.11 | Glosario y documentos | `git diff` | «soles constantes» en `glosario.yaml`; `contrato_validador.md` y `arquitectura.md` al día |

🔎 Nueva huella del cubo: se anota (cambia a propósito) y desde aquí es la referencia de S1-13 a S1-16.

## 3. S1-13 — La evolución muestra los dos años

| # | Comprobación | ✅ si… |
|---|---|---|
| 3.1 | `evolucion anemia Perú` | «Más contexto» trae 2024 y 2025 («X % en 2024 y Y % en 2025»); la cifra de 2024 tiene **marcador y fila de cita propias** (P-02) |
| 3.2 | `--hasta 2024` | Forma anterior 2015–2024; cifra vigente 2024 en «Más contexto» con cita; «Ojo al leer»: «con la forma de medir actual solo hay datos desde 2024»; **no** dice «la más reciente» |
| 3.3 | `--hasta 2018` | Forma anterior 2015–2018; la vigente solo se nombra en «Ojo al leer» |
| 3.4 | Sin dos años en ninguna forma | Sigue «no se puede» |
| 3.5 | Q1 | Única diferencia: la cifra 2024 y su cita. `regresion/Q1.yaml` con `aprobado_por: dueño` y motivo «AD-1 (dueño, 4/11/2026, fila R-04 de decisiones.md)» |
| 3.6 | Test de regresión | Nueva clave exceptuada con el mismo mecanismo que `CLAVE_2022_Q1`; `tests/referencias/q1.json` cambia solo en eso (`git diff`) |
| 3.7 | Prueba sobre la matriz | Prueba automática: toda `evolucion` de la matriz reducida muestra las dos cifras |

⛔ Si Q1 cambia en algo más que lo de 3.5 → consulta C.

## 4. S1-14 — Cruce y efecto

| # | Comprobación | ✅ si… |
|---|---|---|
| 4.1 | H9 | Ninguna capa 1 de `cruce` en la matriz dice «lado a lado» (`grep` sobre las salidas); la ficha larga de CR-01 puede seguir diciéndolo |
| 4.2 | Clave nueva, no global | `git diff -- curados/motor/textos/plantillas/comunes.yaml` vacío; clave nueva en `cruce_efecto.yaml` |
| 4.3 | AD-2 | Frase exacta: «Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió.», en el `mensaje_usuario` de R-CRUCES-07 y en `frases_estandar.efecto`; la primera oración de cada uno sigue igual |
| 4.4 | Solo por el consolidador | `git diff -- reglas/propuestas` vacío; cambios en `ajustes_dueno.py` (con cita AD-2) y gancho `FRASES_ESTANDAR` en `consolida_reglas.py`; vuelvo a correr el consolidador y `reglas.json` sale idéntico al del commit |
| 4.5 | Diff de `reglas.json` acotado | Solo R-CRUCES-07, `frases_estandar.efecto` y R-TERRITORIO-09 |
| 4.6 | Verificaciones de reglas | `vp3_checks.py` sin cierres abiertos; `prueba_guardia.py` 0 fallos; `pap validar-reglas` en verde |
| 4.7 | Corpus y contrato | Span C06 de `corpus_auditor.json` y la frase de `contrato_respuesta.md` actualizados |
| 4.8 | 5 % atribuible | «…del gasto atribuido al departamento de Lima…»; misma cifra; en `Q3.yaml` con `aprobado_por: agente` |
| 4.9 | Q3 | Diferencias solo de 4.3 (dueño, motivo AD-2 fila R-03) y 4.8 (agente) |
| 4.10 | D-01 | Los 4 lugares de `ajustes_dueno.py`; orden: Lima Metropolitana, Lima Región, Callao; `territorio09_lima_orden` exige 3; D-01 cerrada en `consultas_al_dueno.md` |

## 5. S1-15 — Correcciones menores

| # | Comprobación | ✅ si… |
|---|---|---|
| 5.1 | N-3 | `comparacion anemia "Lima Metropolitana" vs "Lima Región"`: «…para Lima Metropolitana y Lima Región»; con límites distintos, un «No permite concluir» por lugar (prueba) |
| 5.2 | N-3 es código | Cambio en `nc_respaldo` (`plantillas.py`); la entrada `decision:` de `parametros_motor.yaml` no cambia |
| 5.3 | H7 | `nivel_actual anemia Perú --anio 2018`: sigue «no se puede»; dice que 2018 solo existe con la forma anterior y ofrece la evolución hasta 2018, que **sí responde** (S1-13) |
| 5.4 | Año sin ninguna serie | `--anio 2010`: «No hay datos de anemia de 2010», sin «con la forma de medir actual» |
| 5.5 | Textos fuera del código | Textos nuevos en `curados/motor/textos/`; corrector sin infracciones; Q1–Q4 sin cambios |

## 6. S1-16 — Verificación y cierre

| # | Comprobación | ✅ si… |
|---|---|---|
| 6.1 | pytest | Lo corro yo en la rama: verde y sin fallos nuevos frente a `pytest_base.txt` |
| 6.2 | Matriz completa | Reporte en `evidencia/adenda/matriz.md` (no sobrescribe `evidencia/matriz.md`): 0 errores, 0 fallos, sin marcadores ni códigos internos |
| 6.3 | Verificación independiente | `encargo_verificador.md` es anterior al informe en `git log`, no trae conclusiones del implementador y pide verificar el factor a mano; `verificacion.md` dice «apto»; hallazgos altos corregidos y verificados de nuevo |
| 6.4 | Documentos | Manual (§5, §6, casos 8 y 12, línea de estado), arquitectura, `cierre.md` §Adenda, `estado.md` (huella nueva, fecha, fase 5a), `plan_slices.md` sin «Antes, cerrar la adenda» |
| 6.5 | Sin referencias rotas | `grep -rn "slice-1-cerrado\|1603698" --include=*.md . \| grep -v evidencia/` solo devuelve líneas que dicen que son de la carpeta anterior |
| 6.6 | `decisiones.md` | Sin filas nuevas; R-03 y R-04 solo se precisan si lo implementado lo obliga |
| 6.7 | Fusión y etiqueta | `slice-1-adenda` fusionada en `main`; etiqueta `slice-1-adenda-cerrada` en GitHub; `pytest_main.txt` en verde; sin `--force` (ver §7 sobre quién fusiona) |

## Comprobaciones transversales (en cada entrega)

- `git diff <base>..HEAD --stat -- curados/capa0 tests/fixtures docs/decisiones.md reglas/propuestas reglas/reglas.json`: todo cambio tiene su historia y su motivo. **Nunca** un dato curado o una dorada cambiados para que pase una prueba.
- Regresión Q1–Q4: cifras, semáforos y confianza iguales. Toda diferencia de texto está en `regresion/Q*.yaml` con quién la aprobó.
- `consultas_al_dueno.md`: leer lo nuevo. Supuestos nuevos con `supuesto: S1-1x`; nada de tipo C rebajado a supuesto.
- Commits con ID de la historia, uno o más por historia; tildes y ñ en todo texto visible.
- La huella del cubo cambia solo en S1-12.

## 7. Entorno en la nube (nuevo: afecta a S1-11 y a `agents.md` §8)

**El problema:** la nube clona GitHub, y ahí no están los crudos (1,3 GB) ni los Parquet. Sin biblioteca, `agents.md` §8 obliga al agente a detenerse en todo lo que toque cifras, que es casi toda la adenda.

**Lo que sí sirve:** `pap calcular` y el motor leen solo Parquet, y `insumos.tabla()` comprueba que cada Parquet sea el que registra su manifiesto. Basta entonces con llevar a la nube la **biblioteca construida** (unos 360 MB), no los crudos.

**Propuesta (pendiente del dueño: X-11):**

1. **En el Mac, una sola vez** (el dueño o Claude Code local): `S1-11` completa tal como está, más un paso nuevo: empaquetar `biblioteca/{dimensiones,estandarizada,indicadores}` en `biblioteca-<huella del cubo>.tar.zst` con su `SHA256SUMS`, y publicarlo.
2. **Dónde publicarlo** (decisión del dueño):

   | Opción | A favor | En contra |
   |---|---|---|
   | **A. Release de GitHub en el mismo repo (recomendada)** | Sin credenciales: el repo ya es público. La nube lo baja con un `curl` en el script de inicio | Publica los Parquet (microdatos anonimizados de INEI y datos del MEF, todos ya públicos). Hay que confirmar que las condiciones de uso permiten redistribuirlos |
   | B. Release en un repo privado de datos | No se publica nada | El entorno de la nube necesita un token con acceso a ese repo |
   | C. Bucket propio (R2, GCS) | Sirve también de respaldo | Cuenta y costo nuevos; dominio en la lista de red del entorno |

3. **En la nube:** el script de inicio del entorno baja el paquete, comprueba `SHA256SUMS` y lo descomprime en `biblioteca/`. Luego, `uv sync` y una prueba de humo: `uv run pap preguntar curados/motor/consultas_minimas/`.
4. **`agents.md` §8:** cambiar «Mac del dueño» por «Mac o entorno en la nube con el paquete de la biblioteca», y dejar el `pap construir` desde crudos solo para el Mac. Lo edita el dueño antes de la adenda, o el agente como primer commit de la adenda (`S1-11: agents.md §8 según X-11`), porque `agents.md` es la regla que el agente sigue.
5. **Pruebas que piden crudos** (candidatas por mencionar `almacen` o `cruda`, a confirmar en la primera corrida: `test_almacen_zstd`, `test_registrar`, `test_foto_pim`, `test_transferencias` y `test_recetas_reales`): en la nube fallarán.
   - Hoy `agents.md` §8 dice que las pruebas que dependen de la biblioteca «fallan, no se saltan», y `conftest.py` vuelve error cualquier `pytest.skip`.
   - Propuesta: una marca nueva, `solo_mac`, registrada en `pyproject.toml`. En la nube se corre `pytest -m "not solo_mac"` y la evidencia lista cuántas quedaron fuera y cuáles. Nada se salta en silencio.
   - Así, la base de la nube sale como «748 menos N, con las N listadas».
   - Cambia una regla de `agents.md`, así que lo decide el dueño (parte de X-11).
6. **Clave del LLM y red** (slice 2, no la adenda): el entorno en la nube necesita la clave como variable secreta y salida de red a la API del proveedor. El tope de gasto real va en la consola del proveedor, porque un registro de uso en un entorno efímero se reinicia en cada sesión (X-13).
7. **S1-11 en la nube:** las tareas 3 y 4 (reconstruir desde los crudos y comparar manifiestos) se hacen en el Mac al armar el paquete. En la nube, S1-11 es: bajar el paquete, comprobar las huellas (`comparar_manifiestos.py` y `insumos.tabla()`), guardar el respaldo y la base de pytest. Hay que reescribir la historia así cuando el dueño decida X-11.
8. **Fusión:** si la nube no puede subir a `main`, el agente sube la rama y abre un PR; el dueño fusiona y pone la etiqueta, o se lo autoriza al agente. S1-16 tarea 4 se lee así.

Aparte, y sin bloquear: el **respaldo externo de los crudos** sigue pendiente. La opción C lo resolvería; con A o B, se puede subir un segundo paquete, privado, con el almacén.
