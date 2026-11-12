# M0-06 — Tablas curadas de 2024: filas, citas y conteos

Generado el 9/11/2026 por el agente implementador. Las tablas viven en `curados/inferencia/`; el comando `uv run pap inferencia validar-tablas` las valida (esquemas en `src/pap/inferencia/tablas_curadas.py`). La revisión del auditor-agente (tarea 8) va aparte en `m0-06_revision.md`.

Todas las páginas de la ficha técnica son las del PDF «2024-5-FichaTecnica.pdf» (recurso `endes-2024-ficha-tecnica`, 21 páginas); la prueba `test_las_citas_a_la_ficha_tecnica_dicen_lo_que_la_ficha_dice_en_esa_pagina` comprueba que las frases citadas estén en esas páginas.

## 1. `diseno_muestral.csv`

Llave: `encuesta, anio, archivo, medicion`.

| archivo | medición | población | peso | estrato | UPM | UPM estable | nivel | uniones | cita |
|---|---|---|---|---|---|---|---|---|---|
| RECH0 | hogar | hogares particulares (residentes habituales y quienes pernoctaron la noche anterior) | `HV005/1e6` | `printf('%02d-%d', HV024, HV022)` | `HV021` | `HV001` | hogar | — | Ficha técnica ENDES 2024 (recurso endes-2024-ficha-tecnica), p. 2 «Los hogares particulares y sus miembros»; §VI p. 11 «Factor Hogar (HV005) … HV001: conglomerado, HV022: estrato, peso=HV005/1000000» y «se encuentra en el módulo RECH0»; curados/capa0/definiciones_endes.yaml:7-10 (peso, estrato = HV024 × HV022, conglomerado = HV021); src/pap/capa0/encuestas.py:137 140 144 |
| RECH23 | hogar | hogares particulares (riqueza y región natural del hogar) | `HV005/1e6` | `printf('%02d-%d', HV024, HV022)` | `HV021` | `HV001` | hogar | RECH23.HHID=RECH0.HHID | Ficha técnica ENDES 2024, §VI p. 11 «Factor Hogar (HV005) … para el cálculo de los indicadores que están relacionados al hogar»; unión declarada RECH23 → RECH0 por HHID en curados/inferencia/archivos_endes_2024.yaml (relaciones); curados/capa0/definiciones_endes.yaml:7-10 |
| RECH6 | hemoglobina | niños de 4 meses a menos de 6 años con hemoglobina medida | `HV005/1e6` | `printf('%02d-%d', HV024, HV022)` | `HV021` | `HV001` | medicion | RECH6.HHID=RECH0.HHID | Ficha técnica ENDES 2024, p. 9 «Registro de los niveles de hemoglobina niños de 4 meses a menores de 6 años»; §VI p. 11 «Factor Hogar (HV005) … se utiliza para … desnutrición y anemia en menores de 5 años»; curados/capa0/definiciones_endes.yaml:7 (peso = HV005/1e6, peso_medicion solo en 2020) y :10; src/pap/capa0/encuestas.py:140 144-145 |
| RECH6 | talla | niños menores de 6 años con talla medida | `HV005/1e6` | `printf('%02d-%d', HV024, HV022)` | `HV021` | `HV001` | medicion | RECH6.HHID=RECH0.HHID | Ficha técnica ENDES 2024, p. 9 «Registro de la medición antropométrica (peso y talla) en niños menores de 6 años»; §VI p. 11 «Factor Hogar (HV005) … se utiliza para … desnutrición y anemia en menores de 5 años»; curados/capa0/definiciones_endes.yaml:7 y :10; src/pap/capa0/encuestas.py:140 144-145 |
| REC0111 | individual_mujer | mujeres de 12 a 49 años de edad | `V005/1e6` | `printf('%02d-%d', V024, V022)` | `V021` | `V001` | individual | — | Ficha técnica ENDES 2024, p. 2 «Todas las mujeres de 12 a 49 años de edad»; §VI p. 11 «Factor Mujer (V005) … V001: conglomerado, V022: estrato, peso=V005/1000000» y «se encuentra en el módulo REC0111»; V021 = «Unidad de muestreo primario - conglomerado» (etiqueta del archivo REC0111 2024); estrato por departamento (V024) × V022 como en curados/capa0/definiciones_endes.yaml:8 (E-01) |
| CSALUD01 | salud_15_mas | una persona de 15 años a más seleccionada por hogar | `PESO15_AMAS/1e6` | `printf('%02d-%d', HV024, HV022)` | `QHCLUSTER` | `HV001` | individual | CSALUD01.HHID=RECH0.HHID | Ficha técnica ENDES 2024, p. 2 «Una persona de 15 años a más de edad por cada hogar particular»; §VI p. 11 «Para personas de 15 años a más (PESO15_AMAS) … qhcluster: conglomerado, HV022: estrato, peso= PESO15_AMAS /1000000» y «se encuentra en el módulo CSALUD01»; HV024 y HV022 vienen de RECH0 (unión declarada CSALUD01 → RECH0 por HHID en archivos_endes_2024.yaml); estrato por departamento × HV022 como en curados/capa0/definiciones_endes.yaml:8 (E-01) |
| CSALUD08 | salud_menores_12 | niños menores de 12 años | `PESOMEN12/1e6` | `printf('%02d-%d', HV024, HV022)` | `QHCLUSTER` | `HV001` | individual | CSALUD08.HHID=RECH0.HHID | Ficha técnica ENDES 2024, p. 2 «Todos los niños menores de 12 años»; §VI p. 11 «Para niños menores de 12 (Pesomen12) … qhcluster: conglomerado, HV022: estrato, peso= Pesomen12/1000000» y «se encuentra en el módulo CSALUD08»; HV024 y HV022 vienen de RECH0 (unión declarada CSALUD08 → RECH0 por HHID en archivos_endes_2024.yaml); estrato por departamento × HV022 como en curados/capa0/definiciones_endes.yaml:8 (E-01) |

No hay fila para RECH1, RECH5, REC21… ni los demás módulos: la ficha no nombra su factor (supuesto M0-06 en `consultas_al_dueno.md`).

## 2. `universos_analiticos.yaml`

| id | unidad | predicados | fuente (líneas exactas) |
|---|---|---|---|
| `nino_hecho` | nino | `HV103 IN (1)` | Población de hecho (durmió en el hogar la noche anterior): curados/capa0/definiciones_endes.yaml:20 («pernocto: true» = HV103 = 1), :27 y :34; src/pap/capa0/encuestas.py:146 («pernocto» = HV103 == 1) y :225-226 (se exige en el universo); Ficha técnica ENDES 2024, §5.1 p. 8 («residentes habituales … que hayan pernoctado la noche anterior») |
| `nino_hecho_hb_medida` | nino | `HV103 IN (1) AND HC55 IN (0)` | curados/capa0/definiciones_endes.yaml:18 («hb_medida: true», HC55 = 0) y :20; src/pap/capa0/encuestas.py:150 («hb_resultado» = HC55), :165 («hb_medida» = hb_resultado == 0), :146 y :219-220, :225-226 |
| `nino_anemia_6_35m_rm363` | nino | `HV103 IN (1) AND HC1 BETWEEN 6 AND 35 AND HC55 IN (0) AND HC57 IN (1, 2, 3, 4)` | Criterio vigente hasta 2023 (RM 363-2022-MINSA): curados/capa0/definiciones_endes.yaml:15-20 (edad_meses [6, 35], hb_medida, «variable_no_nula: true # HC57 en 1–4», pernocto); src/pap/capa0/encuestas.py:148 (HC1), :154 (HC57 en 1–4), :217-218, :221-222, :225-226; Ficha técnica ENDES 2024, punto 6 p. 16 (niños de 6 a 35 meses, RM 363-2022-MINSA) |
| `nino_anemia_6_35m_oms2024` | nino | `HV103 IN (1) AND HC1 BETWEEN 6 AND 35 AND HC55 IN (0) AND HC57A IN (1, 2, 3, 4)` | Criterio vigente (nueva directriz OMS 2024, RM 251-2024-MINSA): curados/capa0/definiciones_endes.yaml:23-27 («HC57A en 1–3; solo desde 2024», universo con los mismos filtros); src/pap/capa0/encuestas.py:148, :155 (HC57A en 1–4), :217-218, :221-222, :225-226; Ficha técnica ENDES 2024, punto 7 p. 16 (niños de 6 a 35 meses, nueva directriz OMS 2024) |
| `nino_dci_0_59m` | nino | `HV103 IN (1) AND HC1 BETWEEN 0 AND 59 AND HC70 BETWEEN -9989 AND 9989` | curados/capa0/definiciones_endes.yaml:28-34 (edad_meses [0, 59], «haz_valido: true # HC70 < 9990», pernocto); src/pap/capa0/encuestas.py:157 (HC70 válido entre −9989 y 9989; HC70 son centésimas de desviación estándar), :169 («haz_valido» = no nulo), :148, :217-218, :223-226; Ficha técnica ENDES 2024, punto 4 p. 15 (menores de cinco años, talla para la edad a menos de dos desviaciones estándar) |

## 3. `territorios.yaml`

| nivel | expr | unidad | como | cita |
|---|---|---|---|---|
| nacional | `TRUE` | `'PE'` | dominio | src/pap/motor/calculo.py:157 («nacional»: la etiqueta «PE» para todas las filas); curados/capa0/dim_indicador.yaml:97-98 (niveles_validos, nivel nacional); Ficha técnica ENDES 2024, §3.7 p. 7 («Anual - Nacional») |
| dominio_subnacional | `HV025 IN (1, 2)` | `CASE HV025 WHEN 1 THEN 'urbano' WHEN 2 THEN 'rural' END` | dominio | src/pap/motor/calculo.py:158 (dominio_subnacional = área); src/pap/capa0/encuestas.py:142 (HV025: 1 urbano, 2 rural); curados/capa0/dim_indicador.yaml:99-104 (dominios urbano y rural); Ficha técnica ENDES 2024, §3.7 p. 7 («Nacional Urbana», «Nacional Rural») |
| departamento | `HV024 <> 7` | `printf('%02d', HV024)` | dominio | src/pap/motor/calculo.py:159 (departamento = HV024 con el 07 en nulo); src/pap/capa0/encuestas.py:141 (HV024 con dos dígitos); curados/capa0/dim_indicador.yaml:105-107 (24 departamentos; el 15 entero incluye Lima Metropolitana y Lima Región; el Callao se publica con nivel CALLAO); Ficha técnica ENDES 2024, §3.7 p. 7 («Cada uno de los 24 departamentos del país y la Provincia Constitucional del Callao») |
| CALLAO | `HV024 = 7` | `'CALLAO'` | dominio | src/pap/capa0/ambitos_lima.py:47 (ubigeo con prefijo 07 = CALLAO) y docstring del módulo (CALLAO: departamento 07); curados/capa0/dim_indicador.yaml:152 (nivel CALLAO); Ficha técnica ENDES 2024, Cuadro N° 1 p. 4 («Provincia Constitucional del Callao») y §3.7 p. 7 |
| LIMA_METROPOLITANA | `substr(UBIGEO, 1, 4) = '1501'` | `'LIMA_METROPOLITANA'` | dominio | src/pap/capa0/ambitos_lima.py:46 (ubigeo con prefijo 1501 = LIMA_METROPOLITANA) y docstring del módulo (provincia 1501, 43 distritos, Ley 31140); curados/capa0/dim_indicador.yaml:108-111 (LIMA_METROPOLITANA; método ubigeo desde 2018); Ficha técnica ENDES 2024, Cuadro N° 1 p. 4 («Lima Metropolitana 1/ Comprende los 43 distritos … Ley 31140») |
| LIMA_REGION | `HV024 = 15 AND substr(UBIGEO, 1, 4) <> '1501'` | `'LIMA_REGION'` | dominio | src/pap/capa0/ambitos_lima.py:45-46 (prefijo 15 y no 1501 = LIMA_REGION) y docstring del módulo (departamento 15 sin la 1501, 9 provincias); curados/capa0/dim_indicador.yaml:130 (nivel LIMA_REGION); Ficha técnica ENDES 2024, Cuadro N° 1 p. 4 («Departamento de Lima 2/ Comprende las provincias: Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón y Yauyos») |

## 4. `perfil_anual.csv`

| campo | valor |
|---|---|
| encuesta | ENDES |
| anio | 2024 |
| marco | Censos Nacionales XII de Población y VII de Vivienda 2017 (CPV 2017) y su cartografía actualizada |
| muestra_maestra | Muestra maestra de 6 submuestras de conglomerados del CPV 2017, con rotación de un tercio por año desde 2022; en 2024 concluye la sexta y para 2025 debe seleccionarse una nueva |
| n_estratos | 240 |
| n_upm | 3254 |
| modo_entrevista | entrevista directa presencial con tablet |
| meses_campo | enero a diciembre |
| ubigeo_minimo | distrito |
| pesos_especiales | PESO15_AMAS (salud, 15 años a más) y PESOMEN12 (salud, menores de 12); HV005A no existe en 2024 |
| clase_cambio | (vacío: lo decide el dueño, E-07) |
| cita | Ficha técnica ENDES 2024 (recurso endes-2024-ficha-tecnica): §3.2 p. 3 (marco CPV 2017); §IV p. 7 (6 submuestras, rotación, «Para el año 2025 se deberán seleccionar una nueva muestra maestra»); Cuadro N° 1 p. 4 (3 254 conglomerados); §3.1 p. 3 (campo «de enero a diciembre» desde 2019); §5.3 y §5.4 p. 10 («Tablet», «ENTREVISTA DIRECTA (presencial)»); §VI p. 11 (PESO15_AMAS, Pesomen12). n_estratos = 240: valores distintos de HV024 × HV022 en RECH0 (estrato de definiciones_endes.yaml:8; src/pap/capa0/encuestas.py:140), comprobado en tests/inferencia/test_tablas_curadas.py. ubigeo_minimo: UBIGEO de 6 dígitos en RECH0 (src/pap/capa0/encuestas.py:143; src/pap/capa0/ambitos_lima.py:36). clase_cambio vacía: 2024 es la única fila de la tabla y la clase la decide el dueño (E-07, K-03) |

## 5. `relacion_entre_anios.csv`

| encuesta | años | relación | UPM estable | cita |
|---|---|---|---|---|
| ENDES | 2023–2024 | conglomerados_repetidos | HV001 | Ficha técnica ENDES 2024 (recurso endes-2024-ficha-tecnica): §3.1 p. 3 «Los conglomerados que tienen la misma numeración en la variable HV001 (conglomerado) en los años 2023 y 2024 son paneles»; §IV p. 7 «se mantendrá el 66.7% de muestra de conglomerados de un año a otro» (rotación desde 2022). No hay microdatos de 2023 en M0: solo se prueba con datos sintéticos |
| ENDES | 2024–2025 | independiente | — | Diseño §7.4 (docs/diseno/motor_inferencia.md): «si la ficha no lo declara, la relación es independiente» (la prueba lleva el aviso «conservadora»). La ficha ENDES 2024 §IV p. 7 solo dice «Para el año 2025 se deberán seleccionar una nueva muestra maestra para continuar con la rotación» y no declara qué conglomerados repite 2025: consulta C-M0-06-1 en backlog/slice-m0/consultas_al_dueno.md |

La fila 2024–2025 **no** es `conglomerados_repetidos` como pedía la historia: la ficha 2024 no declara esa relación para 2025 (consulta **C-M0-06-1**). Solo se prueba el mecanismo (`fraccion_upm_repetidas`) con datos sintéticos; en M0 no hay microdatos de 2023 ni de 2025.

## 6. `cortes_estandar.yaml`

| corte | archivo.variable | unidad | categorías | pendiente | cita de la variable |
|---|---|---|---|---|---|
| area | RECH0.HV025 | hogar | 1=urbano, 2=rural | — | Etiqueta del archivo RECH0 2024: «Área de residencia»; src/pap/capa0/encuestas.py:142 (1 urbano, 2 rural) |
| area | REC0111.V025 | mujer | 1=urbano, 2=rural | — | Etiqueta del archivo REC0111 2024: «Tipo de lugar de residencia» (1 Urbano, 2 Rural) |
| sexo | RECH6.HC27 | nino | 1=hombre, 2=mujer | — | Etiqueta del archivo RECH6 2024: «Sexo» (1 Hombre, 2 Mujer); src/pap/capa0/encuestas.py:149 |
| sexo | RECH1.HV104 | persona_del_hogar | 1=hombre, 2=mujer | — | Etiqueta del archivo RECH1 2024: «Sexo» (1 Hombre, 2 Mujer) |
| sexo | REC21.B4 | hijo_de_mujer | 1=hombre, 2=mujer | — | Etiqueta del archivo REC21 2024: «Sexo del niño» (1 Masculino, 2 Femenino) |
| sexo | CSALUD01.QSSEXO | persona_seleccionada | 1=hombre, 2=mujer | — | Etiqueta del archivo CSALUD01 2024: «Sexo de la persona seleccionada» (1 Hombre, 2 Mujer) |
| grupo_edad | RECH6.HC1 | nino | — | C-M0-06-2 | Etiqueta del archivo RECH6 2024: «Edad en meses» (0 a 59); src/pap/capa0/encuestas.py:148 |
| grupo_edad | RECH1.HV105 | persona_del_hogar | — | C-M0-06-2 | Etiqueta del archivo RECH1 2024: «Edad» (años; 97 = «Mayores de 96», 98 = «No sabe») |
| grupo_edad | REC0111.V013 | mujer | 0=12 a 14 años, 1=15 a 19 años, 2=20 a 24 años, 3=25 a 29 años, 4=30 a 34 años, 5=35 a 39 años, 6=40 a 44 años, 7=45 a 49 años | — | Etiqueta del archivo REC0111 2024: «Edad actual por grupos de 5 años» |
| region_natural | RECH23.SHREGION | hogar | 1=Lima Metropolitana, 2=resto de la Costa, 3=Sierra, 4=Selva | — | Etiqueta del archivo RECH23 2024: «Región natural» (1 Lima metropolitana, 2 Resto Costa, 3 Sierra, 4 Selva) |
| region_natural | REC91.SREGION | mujer | 1=Lima Metropolitana, 2=resto de la Costa, 3=Sierra, 4=Selva | — | Etiqueta del archivo REC91 2024: «Región natural» (1 Lima metropolitana, 2 Resto Costa, 3 Sierra, 4 Selva) |
| quintil_riqueza | RECH23.HV270 | hogar | 1=los más pobres, 2=pobre, 3=medio, 4=rico, 5=más rico | — | Etiqueta del archivo RECH23 2024: «Índice de riqueza» (1 Los más pobres, 2 Pobre, 3 Medio, 4 Rico, 5 Más rico) |
| quintil_riqueza | REC0111.V190 | mujer | 1=los más pobres, 2=pobre, 3=medio, 4=rico, 5=más rico | — | Etiqueta del archivo REC0111 2024: «Índice de riqueza» (1 El más pobre, 2 «Pobrer» [sic], 3 Medio, 4 Rico, 5 Más rico) |

Citas de cada corte:
- **area:** Ficha técnica ENDES 2024, §3.7 p. 7 («Nacional Urbana», «Nacional Rural»); curados/capa0/dim_indicador.yaml:99-104 (dominio_subnacional)
- **sexo:** src/pap/capa0/encuestas.py:149 (sexo del niño: 1 hombre, 2 mujer); etiquetas de los cuatro archivos citadas en cada variable
- **grupo_edad:** Ficha técnica ENDES 2024, §II p. 2 (mujeres de 12 a 49 años, niños menores de 5 años) y punto 6 p. 16 (6 a 35 meses); tramos de la mujer: etiquetas de valor de V013 en REC0111
- **region_natural:** Ficha técnica ENDES 2024, §3.7 p. 7 («Región Natural: Costa, Sierra y Selva» como dominio anual y semestral); las cuatro categorías son las del archivo. Que Costa = Lima Metropolitana + resto de la Costa no lo declara ningún documento registrado: consulta C-M0-06-3
- **quintil_riqueza:** Ficha técnica ENDES 2024, §1.6 y §1.7 p. 13-14 (Índice de Bienestar y Quintil de Riqueza, hogares en cinco partes iguales). La ficha dice que el quintil se presenta en dos versiones (la que preserva el puntaje de la ENDES 2000 y la del año de la encuesta) y ningún archivo dice cuál es HV270: consulta C-M0-06-4

## 7. Conteos (Parquet de 2024, `tests/inferencia/test_tablas_curadas_microdatos.py`)

- Niños de 2024: RECH6 = **20 290**; `endes_nino.parquet` (2024) = **20 290**; la unión RECH6 ↔ RECH1 (HHID, HC0 = HVIDX) ↔ RECH0 (HHID) deja 20 290 filas, sin nulos.

| universo | casos | `endes_nino.parquet` (mismos niños) | cubo `n_muestra` nacional | indicador del cubo |
|---|---|---|---|---|
| `nino_anemia_6_35m_rm363` | **9 959** | igual (conjunto de (id_hogar, idx_nino) idéntico) | 9 959 | `endes_anemia_6_35m` |
| `nino_anemia_6_35m_oms2024` | **9 959** | igual (conjunto de (id_hogar, idx_nino) idéntico) | 9 959 | `endes_anemia_6_35m_oms2024` |
| `nino_dci_0_59m` | **19 511** | igual (conjunto de (id_hogar, idx_nino) idéntico) | 19 511 | `endes_dci_menores_5` |

### Unidades territoriales (aplicando `territorios.yaml` a cada universo)

- `endes_anemia_6_35m`: **30 unidades** (nacional 1, dominio_subnacional 2, departamento 24, CALLAO 1, LIMA_METROPOLITANA 1, LIMA_REGION 1); 30 de 30 con el mismo `n_muestra` que el cubo; conjunto idéntico al del cubo: True.
- `endes_anemia_6_35m_oms2024`: **30 unidades** (nacional 1, dominio_subnacional 2, departamento 24, CALLAO 1, LIMA_METROPOLITANA 1, LIMA_REGION 1); 30 de 30 con el mismo `n_muestra` que el cubo; conjunto idéntico al del cubo: True.
- `endes_dci_menores_5`: **30 unidades** (nacional 1, dominio_subnacional 2, departamento 24, CALLAO 1, LIMA_METROPOLITANA 1, LIMA_REGION 1); 30 de 30 con el mismo `n_muestra` que el cubo; conjunto idéntico al del cubo: True.

## 8. HV001 frente a HV021 en 2024 (solo se constata)

La ficha declara el panel por HV001 y el código usa HV021 como UPM. En RECH0 de 2024: 37 390 filas; HV001 ≠ HV021 en **0**; conglomerados distintos: HV001 3 254, HV021 3 254 (= 3 254 del Cuadro N° 1 de la ficha, p. 4). En REC0111, V001 = HV001 y V021 = HV021 (37 117 mujeres); en CSALUD01 (34 018) y CSALUD08 (41 309), QHCLUSTER = HV001. Prueba: `test_hv001_es_igual_a_hv021_en_2024`. No se decide nada con este resultado.

## 9. Verificaciones

- `uv run pap inferencia validar-tablas` → 6 tablas ✔ (7, 5, 6, 1, 2 y 5 filas), todas con cita; sale con 0.
- `uv run pytest -q -p no:cacheprovider -m regresion_microdatos` → `35 passed, 1369 deselected`.
- Pruebas nuevas: `test_tablas_curadas.py` (18, sin microdatos) y `test_tablas_curadas_microdatos.py` (16, marcadas `regresion_microdatos` + `solo_mac`).
- Suite completa en primer plano: `1403 passed, 1 skipped in 947.44s` (línea base 1369 passed, 1 skipped; +34 pruebas nuevas; 0 fallos).
- Cubo sin cambios: el sha256 de `biblioteca/indicadores/fact_indicador.parquet` empieza con `010ea965`.
- Ningún conteo difirió: no se ajustó ningún dato, tabla curada ni dorada.

## 10. Consultas y supuestos escritos

Tipo C (en «Consultas que bloquean» de `consultas_al_dueno.md`; ninguna bloquea M0-07): **C-M0-06-1** (la ficha 2024 no declara la relación 2024–2025; 2024–2025 = `independiente`, 2023–2024 = `conglomerados_repetidos`), **C-M0-06-2** (tramos del grupo de edad de niños y personas), **C-M0-06-3** (Costa = Lima metropolitana + Resto Costa), **C-M0-06-4** (¿HV270 es el quintil de la ENDES 2000 o el del año?). Supuestos tipo B: bloque «M0-06 —» al final de «Supuestos aplicados».
