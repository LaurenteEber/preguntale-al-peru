# M1-03 — Revisión del auditor-agente (lista para llenar)

**Estado:** revisado el 12/11/2026 por el auditor-agente (verificación independiente, solo lectura): **aprobado con observaciones**. Detalle al final, en «Informe del auditor-agente».

Cómo revisar: abrir el PDF del informe (recurso `endes-2024-informe-ppr`; archivo del almacén en `biblioteca/cruda/capturas/INEI-ENDES/2026-11-12-5/datapackage.json`, campo `path`), ir a la hoja indicada con `pdftotext -layout -f N -l N`, y comprobar en la fila del cuadro la columna «Valor estimado 2024» (2.ª columna de valor tras 2023, antes del intervalo) y «Número de casos sin ponderar». Las cifras de `curados/inferencia/doradas_cortes.csv` las copió el script `evidencia/m1-03_extraer_doradas.py` del texto del PDF (no a mano); el resultado de reproducirlas está en `evidencia/m1-03_doradas_cortes.md`.

## 1. Doradas nuevas (`curados/inferencia/doradas_cortes.csv`, 36 filas)

| # | id_cifra | Receta | Corte | Categoría | Valor | Casos | Cuadro y página impresa | Hoja del PDF | Fila del cuadro | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `DOR-DCI-2024-PE-REGION-1` | endes_dci_menores_5 | region_natural | Costa | 7.3 | 8 047 | Cuadro N.º 04 p. 49 | 51 | Costa | OK |
| 2 | `DOR-DCI-2024-PE-REGION-2` | endes_dci_menores_5 | region_natural | Sierra | 17.6 | 6 162 | Cuadro N.º 04 p. 49 | 51 | Sierra | OK |
| 3 | `DOR-DCI-2024-PE-REGION-3` | endes_dci_menores_5 | region_natural | Selva | 16.3 | 5 302 | Cuadro N.º 04 p. 49 | 51 | Selva | OK |
| 4 | `DOR-DCI-2024-PE-QUINTIL-1` | endes_dci_menores_5 | quintil_riqueza | los más pobres | 22.4 | 5 991 | Cuadro N.º 04 p. 49 | 51 | Quintil inferior | OK |
| 5 | `DOR-DCI-2024-PE-QUINTIL-2` | endes_dci_menores_5 | quintil_riqueza | pobre | 10.8 | 5 218 | Cuadro N.º 04 p. 49 | 51 | Segundo quintil | OK |
| 6 | `DOR-DCI-2024-PE-QUINTIL-3` | endes_dci_menores_5 | quintil_riqueza | medio | 8.5 | 3 835 | Cuadro N.º 04 p. 49 | 51 | Quintil intermedio | OK |
| 7 | `DOR-DCI-2024-PE-QUINTIL-4` | endes_dci_menores_5 | quintil_riqueza | rico | 5.9 | 2 786 | Cuadro N.º 04 p. 49 | 51 | Cuarto quintil | OK |
| 8 | `DOR-DCI-2024-PE-QUINTIL-5` | endes_dci_menores_5 | quintil_riqueza | más rico | 3.5 | 1 681 | Cuadro N.º 04 p. 49 | 51 | Quintil superior | OK |
| 9 | `DOR-DCI-2024-PE-EDAD-1` | endes_dci_menores_5 | grupo_edad | Menores de 36 meses | 13.8 | 11 449 | Cuadro N.º 04 p. 49 | 51 | Menores de 36 meses | OK |
| 10 | `DOR-DCI-2024-PE-EDAD-2` | endes_dci_menores_5 | grupo_edad | De 36 a 59 meses | 9.8 | 8 062 | Cuadro N.º 04 p. 49 | 51 | De 36 a 59 meses | OK |
| 11 | `DOR-ANE-2024-PE-REGION-1` | endes_anemia_6_35m | region_natural | Costa | 36.1 | 4 058 | Cuadro N.º 06 p. 53 | 55 | Costa | OK |
| 12 | `DOR-ANE-2024-PE-REGION-2` | endes_anemia_6_35m | region_natural | Sierra | 53.4 | 3 176 | Cuadro N.º 06 p. 53 | 55 | Sierra | OK |
| 13 | `DOR-ANE-2024-PE-REGION-3` | endes_anemia_6_35m | region_natural | Selva | 48.3 | 2 725 | Cuadro N.º 06 p. 53 | 55 | Selva | OK |
| 14 | `DOR-ANE-2024-PE-QUINTIL-1` | endes_anemia_6_35m | quintil_riqueza | los más pobres | 54.8 | 3 138 | Cuadro N.º 06 p. 53 | 55 | Quintil inferior | OK |
| 15 | `DOR-ANE-2024-PE-QUINTIL-2` | endes_anemia_6_35m | quintil_riqueza | pobre | 47.0 | 2 660 | Cuadro N.º 06 p. 53 | 55 | Segundo quintil | OK |
| 16 | `DOR-ANE-2024-PE-QUINTIL-3` | endes_anemia_6_35m | quintil_riqueza | medio | 38.4 | 1 932 | Cuadro N.º 06 p. 53 | 55 | Quintil intermedio | OK |
| 17 | `DOR-ANE-2024-PE-QUINTIL-4` | endes_anemia_6_35m | quintil_riqueza | rico | 32.8 | 1 406 | Cuadro N.º 06 p. 53 | 55 | Cuarto quintil | OK |
| 18 | `DOR-ANE-2024-PE-QUINTIL-5` | endes_anemia_6_35m | quintil_riqueza | más rico | 31.1 | 823 | Cuadro N.º 06 p. 53 | 55 | Quintil superior | OK |
| 19 | `DOR-ANE-2024-PE-EDAD-1` | endes_anemia_6_35m | grupo_edad | 6 a 8 meses | 68.1 | 968 | Cuadro N.º 06B p. 55 | 57 | 6 a 8 meses | OK |
| 20 | `DOR-ANE-2024-PE-EDAD-2` | endes_anemia_6_35m | grupo_edad | 9 a 11 meses | 66.3 | 1 059 | Cuadro N.º 06B p. 55 | 57 | 9 a 11 meses | OK |
| 21 | `DOR-ANE-2024-PE-EDAD-3` | endes_anemia_6_35m | grupo_edad | 12 a 17 meses | 53.1 | 1 977 | Cuadro N.º 06B p. 55 | 57 | 12 a 17 meses | OK |
| 22 | `DOR-ANE-2024-PE-EDAD-4` | endes_anemia_6_35m | grupo_edad | 18 a 23 meses | 40.2 | 1 961 | Cuadro N.º 06B p. 55 | 57 | 18 a 23 meses | OK |
| 23 | `DOR-ANE-2024-PE-EDAD-5` | endes_anemia_6_35m | grupo_edad | 24 a 35 meses | 29.0 | 3 994 | Cuadro N.º 06B p. 55 | 57 | 24 a 35 meses | OK |
| 24 | `DOR-ANEOMS-2024-PE-REGION-1` | endes_anemia_6_35m_oms2024 | region_natural | Costa | 27.0 | 4 058 | Cuadro N.º 6.1 p. 56 | 58 | Costa | OK |
| 25 | `DOR-ANEOMS-2024-PE-REGION-2` | endes_anemia_6_35m_oms2024 | region_natural | Sierra | 43.1 | 3 176 | Cuadro N.º 6.1 p. 56 | 58 | Sierra | OK |
| 26 | `DOR-ANEOMS-2024-PE-REGION-3` | endes_anemia_6_35m_oms2024 | region_natural | Selva | 44.1 | 2 725 | Cuadro N.º 6.1 p. 56 | 58 | Selva | OK |
| 27 | `DOR-ANEOMS-2024-PE-QUINTIL-1` | endes_anemia_6_35m_oms2024 | quintil_riqueza | los más pobres | 47.5 | 3 138 | Cuadro N.º 6.1 p. 56 | 58 | Quintil inferior | OK |
| 28 | `DOR-ANEOMS-2024-PE-QUINTIL-2` | endes_anemia_6_35m_oms2024 | quintil_riqueza | pobre | 37.2 | 2 660 | Cuadro N.º 6.1 p. 56 | 58 | Segundo quintil | OK |
| 29 | `DOR-ANEOMS-2024-PE-QUINTIL-3` | endes_anemia_6_35m_oms2024 | quintil_riqueza | medio | 29.7 | 1 932 | Cuadro N.º 6.1 p. 56 | 58 | Quintil intermedio | OK |
| 30 | `DOR-ANEOMS-2024-PE-QUINTIL-4` | endes_anemia_6_35m_oms2024 | quintil_riqueza | rico | 24.5 | 1 406 | Cuadro N.º 6.1 p. 56 | 58 | Cuarto quintil | OK |
| 31 | `DOR-ANEOMS-2024-PE-QUINTIL-5` | endes_anemia_6_35m_oms2024 | quintil_riqueza | más rico | 22.8 | 823 | Cuadro N.º 6.1 p. 56 | 58 | Quintil superior | OK |
| 32 | `DOR-ANEOMS-2024-PE-EDAD-1` | endes_anemia_6_35m_oms2024 | grupo_edad | 6 a 8 meses | 51.8 | 968 | Cuadro N.º 6.1B p. 58 | 60 | 6 a 8 meses | OK |
| 33 | `DOR-ANEOMS-2024-PE-EDAD-2` | endes_anemia_6_35m_oms2024 | grupo_edad | 9 a 11 meses | 51.8 | 1 059 | Cuadro N.º 6.1B p. 58 | 60 | 9 a 11 meses | OK |
| 34 | `DOR-ANEOMS-2024-PE-EDAD-3` | endes_anemia_6_35m_oms2024 | grupo_edad | 12 a 17 meses | 36.0 | 1 977 | Cuadro N.º 6.1B p. 58 | 60 | 12 a 17 meses | OK |
| 35 | `DOR-ANEOMS-2024-PE-EDAD-4` | endes_anemia_6_35m_oms2024 | grupo_edad | 18 a 23 meses | 25.4 | 1 961 | Cuadro N.º 6.1B p. 58 | 60 | 18 a 23 meses | OK |
| 36 | `DOR-ANEOMS-2024-PE-EDAD-5` | endes_anemia_6_35m_oms2024 | grupo_edad | 24 a 35 meses | 31.6 | 3 994 | Cuadro N.º 6.1B p. 58 | 60 | 24 a 35 meses | OK |

Puntos a comprobar en el conjunto (marcar):

- [ ] Los 36 valores y casos coinciden con el PDF (columnas «Valor estimado 2024» y «Número de casos sin ponderar»).
- [ ] Ninguna cifra está entre paréntesis en el PDF (referencial); el script se detiene si alguna lo estuviera.
- [ ] Cuadros y páginas: 04 → p. 49 (hoja 51); 06 → p. 53 (hoja 55); 06B → p. 55 (hoja 57); 6.1 → p. 56 (hoja 58); 6.1B → p. 58 (hoja 60).
- [ ] La correspondencia fila del INEI → categoría del corte es la esperada: «Quintil inferior» = «los más pobres» (HV270 = 1) … «Quintil superior» = «más rico» (5); «Costa» = SHREGION 1 y 2.
- [ ] Las tres cifras de referencia del auditor del supervisor coinciden: Costa 7,3 / 36,1 / 27,0; quintil inferior 22,4 / 54,8 / 47,5.
- [ ] `cifras_doradas.csv` no cambió (`git diff` vacío).
- [ ] Las 36 se reproducen con las recetas dentro de ±0,1 pp y con los mismos casos (`evidencia/m1-03_doradas_cortes.md`: diferencia 0,0 en todas).

## 2. Tabla de mediciones (`curados/inferencia/mediciones.yaml`)

La declara una persona; el verificador elige con ella el universo de un plan compuesto. Etiquetas tomadas de `biblioteca/variables/variables.parquet` (columna `etiqueta_original`, archivo RECH6 2024).

### Medición `hemoglobina` — RECH6 — batería: Registro de los niveles de hemoglobina de niñas y niños de 4 meses a menos de 6 años

| Variable | Etiqueta original (RECH6 2024) | Veredicto |
|---|---|---|
| HC53 | Nivel de hemoglobina (g/dl-1 decimal) | OK |
| HC55 | Resultado de medir (hemoglobina) | OK |
| HC56 | Nivel de hemoglobina ajustado por altitud (g/dl-1 decimal) RM 363-2022-MINSA | OK |
| HC56A | Nivel de hemoglobina ajustado por altitud (g/dl-1 decimal) NUEVA DIRECTRIZ OMS 2 | OK |
| HC57 | Nivel de anemia RM 363-2022-MINSA | OK |
| HC57A | Nivel de anemia NUEVA DIRECTRIZ OMS 2024/RM 251-2024-MINSA | OK |

### Medición `talla` — RECH6 — batería: Registro de la medición antropométrica (peso y talla) en niñas y niños menores de 6 años

| Variable | Etiqueta original (RECH6 2024) | Veredicto |
|---|---|---|
| HC2 | Peso en kilogramos (1 dec.) | OK |
| HC3 | Altura en centímetros (1 dec.) | OK |
| HC4 | Talla/Edad percentil | OK |
| HC5 | Talla/Edad Desviación Estándar | OK |
| HC6 | Talla/Edad porcentaje de la mediana de referencia | OK |
| HC7 | Peso/Edad percentil | OK |
| HC8 | Peso/Edad Desviación Estándar | OK |
| HC9 | Peso/Edad porcentaje de la mediana de referencia | OK |
| HC10 | Peso/Talla percentil | OK |
| HC11 | Peso/Talla Desviación Estándar | OK |
| HC12 | Peso/Talla Porcentaje de la mediana de referencia | OK |
| HC13 | Razón por la cual el niño no se midió | OK |
| HC15 | El niño se midió acostado o de pie | OK |
| HC70 | Talla/Edad de la Desviación Estándar de la mediana de referencia (según la OMS) | OK |
| HC71 | Peso/Edad de la Desviación Estándar de la mediana de referencia (según la OMS) | OK |
| HC72 | Peso/Talla Desviación Estándar de la mediana de referencia (según la OMS) | OK |
| HC73 | Desviación Estándar del IMC (según la OMS) | OK |

Variables de RECH6 que **no** se declararon como medición, para que el auditor confirme que está bien: HC1 (edad en meses), HC19 (año de la medición; dudoso), HC52 (consentimiento), HC58 (aceptación de envío a un especialista), HC27 (sexo), HC30–HC33 (fechas de nacimiento), HC51 y HC60–HC68 (padres, educación de la madre, orden de nacimiento).

- [ ] Cada variable está en la medición correcta y ninguna está en dos.
- [ ] HC19 queda fuera (o se agrega, con la razón).
- [ ] Cada medición coincide con `aplica_a.mediciones` de `universos_analiticos.yaml` (`hemoglobina` → `nino_hecho_hb_medida`; `talla` → `nino_dci_0_59m`; las dos → `nino_hecho`).
- [ ] La cita de cada medición dice dónde (ficha técnica p. 9 y etiquetas del archivo).

## 3. Otros puntos para el auditor

- [ ] `archivos_endes_2024.yaml`: RECH23–RECH0 pasó de `n:1` a `1:1` (37 390 filas en ambas; medido) y REC42, RE223132, RE516171 y RE758081 frente a REC0111 a `1:0..1` (34 252 de 37 117; medido). `test_las_cardinalidades_declaradas_se_cumplen_en_los_parquet_de_2024` lo comprueba contra los Parquet.
- [ ] La unión por el padre común rechaza lo que no es 1:1 ni 1:0..1 (`test_una_tabla_hermana_declarada_n_a_1_no_se_alcanza_y_el_corte_falla`, `test_ruta_de_uniones_admite_1_a_0_o_1_y_rechaza_lo_que_no_es_1_a_1`) y, si una tabla declarada 1:1 repitiera filas, el control de filas de la unidad detiene el plan (`…_que_repite_filas_detiene_el_plan…`).
- [ ] `cortes_estandar.yaml`: se quitó `pendiente: M1-03` de RECH6.HC1; ningún valor decidido por el dueño cambió (tramos, rótulos, `agrupa`).
- [ ] Recetas: `cortes_permitidos` ahora incluye `grupo_edad`, `region_natural` y `quintil_riqueza`; `cortes_no_permitidos` quedó vacío; versión 0.3.0. Estados, doradas y tolerancias no cambiaron.
- [ ] Las 90 filas: diferencia 0 frente al cubo (`pap inferencia receta <id> --anio 2024 --comparar-cubo` × 3 y `test_recetas_microdatos.py`); `fact_indicador.parquet` sigue con sha256 `010ea965…`.
- [ ] HC55 = 0: con el universo de la receta (`nino_hecho_hb_medida`) y con la base común (`nino_hecho`) los casos son idénticos en las tres recetas (9 959, 9 959 y 19 511); la prueba sintética muestra que un niño con HC55 ≠ 0 sale de u.
- [ ] Supuestos tipo B aplicados: M1-03-s1 … s9 en `consultas_al_dueno.md` (en especial s1, s2 y s4).

## Veredicto

- Doradas nuevas: ____________________
- Tabla de mediciones: ____________________
- Global (aprobado / aprobado con cambios / rechazado): ____________________
- Fecha y quién revisó: ____________________


## Informe del auditor-agente (12/11/2026)

- **Cómo:** leyó las hojas 51, 55, 57, 58 y 60 del informe registrado (`endes-2024-informe-ppr`, sha256 comprobado) con `pdftotext -layout`; reprodujo las 36 cifras con una consulta propia en duckdb, escrita desde cero (sin usar el script del implementador); corrió las 3 recetas con `--comparar-cubo` (30 de 30 filas cada una, diferencia 0, doradas de siempre 3/3, 9/9 y 9/9); `test_m103_microdatos.py` 12 de 12; cubo `010ea965…`; `curados/capa0/` sin cambios.
- **Doradas (36 filas):** las 36 coinciden con el PDF en valor, decimales, casos sin ponderar, cuadro, página impresa y categoría (HV270 = 1 «Quintil inferior», SHREGION 1 y 2 «Costa», tramos de HC1 por indicador). Ninguna cifra de 2024 va entre paréntesis.
- **Tabla de mediciones:** las 6 variables de hemoglobina y las 17 de talla tienen las etiquetas del índice 2024; ninguna está en las dos; las que quedan fuera no son mediciones. Universos: hemoglobina → `nino_hecho_hb_medida`, talla → `nino_dci_0_59m`, las dos → `nino_hecho`.
- **Cardinalidades:** RECH23–RECH0 1:1 (37 390 y 37 390, sin huérfanos); REC42, RE223132, RE516171 y RE758081 1:0..1 frente a REC0111 (34 252 filas, 34 252 CASEID distintos, 0 sin su mujer; 2 865 mujeres sin pareja).
- **Observaciones (no bloquean):**
  1. El quintil superior de la desnutrición crónica tiene CV 14,7 %, cerca del 15 % (fue referencial en 2019, 2020 y 2022): vigilarlo en M2.
  2. Un plan compuesto con una variable de talla recibe `nino_dci_0_59m`, que exige HC70 válido: excluiría a niños pesados sin índice talla/edad válido (322 filas con HC13 ≠ 0). Coherente con «talla»; el dueño puede querer una medición «peso» aparte más adelante.
  3. La lista de variables no declaradas no menciona HC16 ni ID1 (bien fuera).
  4. REC91 (1:1) y REC84DV, CSALUD01 y Programas_Sociales_x_Hogar (1:0..1) siguen declaradas `n:1` sin medir: conservador y correcto por ahora.
- **Veredicto:** doradas aprobadas (36/36); tabla de mediciones aprobada; global **aprobado con observaciones**.
- **No verificó:** la ficha técnica p. 9 que citan las mediciones, ni las pruebas sintéticas de unión.
- **Prueba de regresión que propuso:** se agregaron las cardinalidades medidas (`tests/inferencia/test_m103_auditor.py`). La parte que recalcula cifras con SQL propio no se agregó: el proyecto calcula cifras solo en el ejecutor y las recetas (P-01), y la reproducción de las doradas ya la prueban `test_m103_microdatos.py` y `--comparar-cubo`.
