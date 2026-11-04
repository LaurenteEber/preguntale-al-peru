# Encargo S1-16 — Verificación independiente de la adenda del slice 1

Quién: un subagente nuevo, distinto del implementador (P-06). Rama `slice-1-adenda`, base `0166c59` (`main` al empezar la adenda). El verificador **no edita** código, datos, reglas ni documentos: solo lee, corre pruebas y comandos, y entrega su informe. Las salidas que genere van bajo `salidas/` (fuera de git) o en un directorio temporal, nunca dentro de `backlog/`, `src/`, `curados/` ni `tests/`.

Entorno: Claude Code en la nube (X-11). La biblioteca está en `biblioteca/` (bajada del release y recalculada con `pap calcular`); el respaldo previo a la adenda está en `biblioteca/_respaldo_pre_adenda/`. Las pruebas que necesitan los crudos llevan la marca `solo_mac`: se corre `uv run pytest -q -m "not solo_mac"`.

## Qué leer

- `agents.md` (reglas del trabajo; §5.1 dice cuándo el agente puede aprobar una diferencia de texto).
- `backlog/slice-1/adenda/README.md` (definición de hecho de la adenda) y las historias `S1-11` a `S1-16`.
- `docs/decisiones.md`: filas G-01, G-07, E-06, R-03 (AD-2), R-04 (AD-1), T-03.
- Lo que haga falta del código (`src/pap/motor/`), de las plantillas (`curados/motor/`) y de las pruebas.

No hace falta leer los informes de evidencia del implementador para llegar a una conclusión; si los usa, se comprueban por cuenta propia.

## Qué comprobar, punto por punto de la definición de hecho

1. **Biblioteca.** El manifiesto del respaldo (`git show 0166c59:biblioteca/indicadores/manifiesto_p1_indicadores.json`) registra el cubo `sha256:ba1fbc55…` y la copia de `biblioteca/_respaldo_pre_adenda/indicadores/fact_indicador.parquet` tiene esa huella. Las filas que ya existían en ese cubo son iguales en el cubo actual en todas sus columnas salvo `version_tabla` (comparación propia, p. ej. con pandas o DuckDB). Las únicas filas nuevas son `medida = devengado_constante` de `gasto_ex_pan` y `gasto_ex_pan_opcion_c`. Las columnas `anio_base_deflactor` (entero) y `factor_deflactor` (doble) son nulas en las demás filas; `version_tabla` = `1.2.0`. Nada cambió en `biblioteca/cruda/` ni en `curados/insumos.lock.yaml` (`git diff 0166c59..HEAD --stat` sobre esas rutas).
2. **Soles constantes.** **A mano, desde `biblioteca/dimensiones/dim_ipc.parquet`**: el promedio anual (`ipc_prom_anual`) de 2023 y de 2025 y el factor 2023→2025 = IPC 2025 / IPC 2023; que coincida con `factor_deflactor` del cubo; que `valor` = devengado × factor en todas las filas `devengado_constante`; que los montos nominales nacionales de control no cambiaron (G-07: 2 179 / 2 429 / 2 456 millones). Que el año base no está escrito a mano en `calculo.py` ni en `respuesta.py`, y que coincide con el del validador (`reglas_etapa1_3.py`, R-GASTO-12: `ctx.anio_actual - 1`). Correr `uv run pap preguntar --intencion evolucion --tema gasto_publico --territorio "Perú" --salida <tmp>` y leer la respuesta: compara 2023 con 2025 en soles de 2025, sin diferencia ni porcentaje, con el mensaje de R-GASTO-12 en «Ojo al leer», sin `bloquear_cruce`; «Para citar» da el monto nominal de cada año y el factor. Una cifra de un solo año (`--intencion nivel_actual --tema gasto_publico --territorio "Perú"`) sigue en soles corrientes.
3. **Hallazgos de la revisión.** Para cada uno, reproducir el caso y leer la respuesta:
   - **H11 (AD-1):** `evolucion anemia Perú`: «Más contexto» trae la cifra vigente de 2024 junto a la de 2025, y la de 2024 tiene su marcador en `texto_con_marcadores` y su línea en «Para citar».
   - **N-2 y A-H6:** `--hasta 2024` responde con la forma anterior 2015–2024, muestra la vigente de 2024 en «Más contexto» con su cita, el «Ojo al leer» dice que con la forma actual solo hay datos desde 2024 y no llama «la más reciente» a 2024. `--hasta 2018` responde con la forma anterior 2015–2018. Si ninguna forma tiene dos años, sigue el «no se puede».
   - **H9:** ninguna capa 1 de `cruce` dice «lado a lado» (probar al menos un departamento, Lima Metropolitana y el país). `git diff 0166c59..HEAD -- curados/motor/textos/plantillas/comunes.yaml` debe salir vacío.
   - **H12 (AD-2):** la frase exacta «Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió.» en el `mensaje_usuario` de R-CRUCES-07 y en `lenguaje.frases_estandar.efecto` de `reglas/reglas.json`, con la primera oración de cada uno sin cambiar. `git diff 0166c59..HEAD -- reglas/propuestas` vacío. Volver a correr `python3 reglas/consolidador/consolida_reglas.py` y confirmar que `reglas.json` no cambia (`git status`); el diff de `reglas.json` contra la base solo toca R-CRUCES-07, `frases_estandar.efecto` y R-TERRITORIO-09. Correr `python3 -I reglas/consolidador/pruebas/vp3_checks.py .` (sin cierres abiertos), `python3 reglas/consolidador/pruebas/prueba_guardia.py` (0 fallos) y `uv run pap validar-reglas`. La respuesta de efecto de Q3 no se contradice; el porcentaje atribuible dice de qué total es.
   - **D-01:** R-TERRITORIO-09 ofrece para «Lima» Lima Metropolitana, Lima Región y Callao, en ese orden.
   - **N-3:** `--intencion comparacion --tema anemia --territorio "Lima Metropolitana" --comparar-con "Lima Región"`: el «No permite concluir» nombra los dos lugares.
   - **H7:** `--intencion nivel_actual --tema anemia --territorio "Perú" --anio 2018` sigue siendo «no se puede», dice que 2018 solo existe con la forma anterior y ofrece la evolución hasta 2018, que sí responde. Con `--anio 2010`: «No hay datos de anemia de 2010», sin «con la forma de medir actual».
4. **Regresión Q1–Q4.** `uv run pytest -q tests/test_regresion_q1_q4.py` en verde. Leer la prueba para confirmar que compara cifras, semáforos, confianza y reglas firmes contra `tests/referencias/`. Leer `backlog/slice-1/evidencia/regresion/Q1.yaml` y `Q3.yaml`: cada diferencia nueva de la adenda tiene quién la aprobó y por qué. Las de AD-1 y AD-2 deben decir `aprobado_por: dueño` con su motivo; las del agente deben cumplir `agents.md` §5.1 (juzgarlo por cuenta propia). Q2 y Q4 sin diferencias nuevas.
5. **Pruebas y matriz.** `uv run pytest -q -m "not solo_mac"` sin fallos (comparar con `backlog/slice-1/evidencia/adenda/pytest_base.txt`, que registra la base de la nube). La matriz completa: leer `backlog/slice-1/evidencia/adenda/matriz.md` (0 errores, 0 fallos); si hay tiempo, volver a correrla con `uv run python tests/matriz/correr.py --salida salidas/matriz_verificador` (unos 5 minutos) sin `--reporte`.
6. **Cambios sin historia.** `git diff 0166c59..HEAD --stat -- curados/capa0 tests/fixtures docs/decisiones.md reglas/propuestas tests/referencias`: todo cambio debe tener su historia y su motivo; nunca un dato curado o una dorada cambiados para que pase una prueba.

## Criterios

Cada punto queda «cumple», «cumple con observación» o «no cumple», con evidencia (comando y lo que devolvió, o `archivo:línea`). Severidad de lo que se encuentre: **bloqueante** (cambia una cifra, un semáforo o la confianza sin decisión; una regla editada a mano; un criterio de la definición de hecho no cumplido), **alto** (texto que afirma algo que los datos no respaldan o contradice una decisión), **medio** y **bajo**. Lo que ya fallaba en la base no cuenta como hallazgo de la adenda (decirlo como observación).

## Qué entregar

El texto completo de `backlog/slice-1/evidencia/adenda/verificacion.md`, en español sencillo: veredicto («apto», «apto con observaciones» o «no apto»); una tabla por punto de la definición de hecho (punto, estado, evidencia); el cálculo a mano del factor del IPC; los hallazgos con su severidad; las pruebas y comandos corridos con su resultado.
