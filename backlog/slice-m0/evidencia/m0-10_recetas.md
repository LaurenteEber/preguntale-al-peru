# M0-10 — Recetas 2024 que igualan al cubo: evidencia

Código: `src/pap/inferencia/recetas.py` (esquema, `validar`, `calcular`, `comparar_fila`, `reproducir_doradas`) y el comando `pap inferencia receta ID --anio 2024 [--comparar-cubo]` / `pap inferencia validar-recetas` (`src/pap/cli.py`). Recetas: `curados/inferencia/recetas/{endes_anemia_6_35m,endes_anemia_6_35m_oms2024,endes_dci_menores_5}.yaml`. Los planes de las pruebas anteriores (`tests/inferencia/recetas_m0.py`) ahora salen de esos YAML (hay una sola definición; los `id_plan` son idénticos a los de M0-07). Pruebas: `tests/inferencia/test_recetas.py` (38, sin microdatos) y `tests/inferencia/test_recetas_microdatos.py` (18, `regresion_microdatos` + `solo_mac`). Filas: `m0-10_recetas_vs_cubo.csv` (se regenera con `uv run python tests/inferencia/comparar_m10.py`).

## Método

Para cada receta y cada uno de los 6 niveles de `territorios.yaml` (30 unidades): `Receta.a_plan` → `verificar` (con DuckDB endurecido, sobre `biblioteca/microdatos/ENDES/2024/`) → `Ejecutor` con `PoolEjecutor` → `compuertas.evaluar`. No se tocó R ni `verificador_r/`. Las 90 filas se comparan con `m0-00_filas_cubo_2024.csv` (cubo `010ea965…`, sin cambios) con los criterios de la definición de hecho del slice, punto 1:

- valor, ee, cv, IC y deff **redondeados a 8 decimales**, |dif| ≤ 1e-8 (contado en unidades de 1e-8);
- `n_muestra` y `gl` idénticos;
- n efectivo contra mín(n, n efectivo del cubo) (el ejecutor lo topa en n; el cubo no: 12 filas);
- **sin redondear**, contra `calculo._svy_niveles` (calculado en la prueba sobre `endes_nino.parquet` en solo lectura, con las mismas etiquetas que `_calcular_endes`, incluidos los tres ámbitos de Lima): |dif| ≤ 1e-12.

## Resultado: 90 filas, 0 diferencias

| Columna | Máx. \|dif\| redondeada (vs cubo) | Máx. \|dif\| sin redondear (vs `_svy_niveles`) | Filas fuera |
|---|---|---|---|
| valor | 0 | 0 | 0 |
| ee | 0 | 0 | 0 |
| cv | 0 | 0 | 0 |
| ic_inf | 0 | 0 | 0 |
| ic_sup | 0 | 0 | 0 |
| deff | 0 | 0 | 0 |
| gl | 0 | 0 | 0 |
| n_muestra | 0 | 0 | 0 |
| n_efectivo | 0 | 0 | 0 |

Redondeada a 8 decimales, la cifra nueva es exactamente la del cubo; sin redondear es idéntica bit a bit a `_svy_niveles` (el adaptador hace la misma llamada a `svy`). La primera lectura de M0-08 (sin redondear contra el cubo) daba ≤ 4,99e-9, que es el redondeo del propio cubo. Sin consulta tipo C por cifras.

## Doradas de 2024 (E-05: ENDES ±0,1 pp)

| Receta | Doradas | Máx. \|dif\| | Resultado |
|---|---|---|---|
| `endes_anemia_6_35m` | 9 (nacional, Huancavelica, Puno, Loreto, Ucayali, Cajamarca, Lima Metropolitana, urbano, rural) | 0,0 pp | 9 de 9 |
| `endes_anemia_6_35m_oms2024` | 9 (las mismas) | 0,0 pp | 9 de 9 |
| `endes_dci_menores_5` | 3 (nacional 12,1; urbano 8,5; rural 20,9) con casos publicados (19 511; 13 565; 5 946) y CV (2,8; 3,7; 3,9) | 0,0 pp | 3 de 3, casos exactos y CV dentro de 0,1 |

Las doradas viven en cada YAML con su cita y `validar-recetas` exige que coincidan con `cifras_doradas.csv`. Lo que no se comparó: las doradas de otros años (la receta vale solo 2024).

## Compuertas (R-ENC-02 a 04) contra `m0-00_estados_cubo.csv`

Las 90 filas dan el mismo estado y las mismas reglas disparadas (`regla:acción:motivo`): 85 publicables y 5 referenciales, igual que el cubo. La confianza de lo publicable es `baja` en las 3 recetas porque no están `verificado` (supuesto M0-09); `coincide_oficial` solo se activa donde la dorada de ese dominio pasa.

## Recetas, cortes y universos

- `transformaciones: []` en las 3; ninguna necesitó algo que no esté en el código actual.
- Cortes permitidos: `area` y `sexo` (el verificador los deja pasar). `grupo_edad`, `region_natural` y `quintil_riqueza` quedan no permitidos con su consulta (C-M0-06-2, -3, -4); la prueba comprueba que el verificador los rechaza.
- Universos: la receta de anemia declara `nino_hecho_hb_medida` y la de DCI `nino_hecho`; el verificador siempre agrega la base común `nino_hecho`. HC55 = 0 es redundante con HC57/HC57A en 1–4 (0 niños de 6 a 35 meses con nivel y HC55 ≠ 0): consulta no bloqueante **D-M0-10-1**.
- `dim_indicador.yaml`: campo `receta` en los 3 indicadores. Ni `calculo` ni `capa0.indicadores` validan campos desconocidos ni lo usan: el hash del cubo sigue `010ea965381c…`.

## Estado de las recetas y criterios

- Las 3 recetas quedan en **`estado: revisado`, `pendiente: visto_dueno`**. `verificado` **no** se pone: falta el visto del dueño (K-03). Las tres condiciones: recetas igualan al cubo ✔, reproducen sus doradas ✔, visto del dueño **pendiente**.
- La revisión del auditor-agente (`m0-10_revision.md`) la hace la persona que coordina; no está en esta evidencia.

## Pruebas

- `uv run pytest -q -p no:cacheprovider -m regresion_microdatos`: 74 passed, 1696 deselected.
- Suite completa (`uv run pytest -q -p no:cacheprovider -rf`): 1769 passed, 1 skipped, 0 fallos (1711 de la base + 56 nuevas de M0-10 + 2 de `test_esperados_r.py` que ahora pasan). Los 2 fallos intencionales de `test_esperados_r.py` ya no fallan: `HEAD` (`f61aed0`) trae `tests/esperados/r_survey_sintetico.csv`; esta historia no corrió R.
