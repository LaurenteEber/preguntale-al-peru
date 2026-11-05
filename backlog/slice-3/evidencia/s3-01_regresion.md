# S3-01 — Evidencia

Historia: [S3-01](../S3-01-decisiones-motor.md). Base de pytest del slice: [pytest_base.txt](pytest_base.txt) (944 pasan, 0 fallos).

Verificación final: `uv run pytest -q -m "not solo_mac" -p no:cacheprovider`: 960 pasan, 0 fallan, 34 fuera (`solo_mac` y similares). Son los 944 de la base más 16 nuevas (`tests/test_s3_01_decisiones.py`).

## Criterios de aceptación

| Criterio | Resultado | Dónde se ve |
|---|---|---|
| Q2 con el conteo y Q3 con el gasto del mismo año, como claves exceptuadas; ninguna otra cifra cambia | cumplido | `tests/test_regresion_q1_q4.py`: `CLAVE_2024_Q3` (exceptuada igual que `CLAVE_2022_Q1` y `CLAVE_2024_Q1`, en `test_planes` y en `test_respuestas`). El conteo de Q2 no es una cifra nueva (es el numerador y el denominador de la misma cifra del SIEN): entra como tarjeta nueva, aprobada en `../../slice-1/evidencia/regresion/Q2.yaml`. `tests/test_s3_01_decisiones.py::test_x02_q2_trae_el_conteo_sien` y `::test_x03_q3_trae_el_gasto_del_mismo_anio` |
| La prueba de X-04 sobre un caso con `ic_inei` está en verde | cumplido | `tests/test_s3_01_decisiones.py::test_x04_un_solo_intervalo_con_ic_inei_distinto_del_propio`: Moquegua, pobreza monetaria 2025 (ámbar). El intervalo propio (5,5 a 10,7) redondea a «entre 5 % y 11 %» y el del INEI (5,3 a 10,4) a «entre 5 % y 10 %». Con `uno` la capa 1 muestra el del INEI; con `ambos`, el propio; las cifras son iguales. Q1–Q4 no tienen ningún cambio por X-04 |
| Los `.md` de Q1–Q4 son idénticos tras mover los rótulos | cumplido | ver «Rótulos» abajo |
| X-01 aplicada solo si el dueño la aprobó; si no, queda anotada | **no aplicada** (el dueño no la aprobó) | `que_hacer.yaml` → `anemia.revisado_dueno` sigue en `false`; anotada en `../consultas_al_dueno.md` («Pendientes del dueño que siguen abiertos»); la respuesta conserva «(texto pendiente de revisión)» |
| Toda cita de Q1–Q4 con dorada lleva su `url` oficial | cumplido | tabla de enlaces abajo; `tests/test_s3_01_decisiones.py::test_cada_cita_lleva_su_url_oficial[q1..q4]` |

## Decisiones aplicadas (`parametros_motor.yaml` → `pendientes_dueno`)

`pendiente:` pasó a `decision:` con su fila: `mostrar_conteo_sien` = `true` (X-02, S-01), `cr01_mismo_anio` = `true` (X-03, R-03), `intervalo_visible` = `uno` (X-04, E-04). Las filas E-04, S-01 y R-03 de `docs/decisiones.md` ya no dicen «se aplica al empezar el slice 3…». P-02 agrega que la cita lleva el enlace. R-06 y X-01 no cambian.

## Cambios de Q1–Q4 (todos aprobados en `slice-1/evidencia/regresion/Q*.yaml`)

| Q | Cambio | Decisión |
|---|---|---|
| Q1 | solo los enlaces de las 4 citas | plan_slices.md, slice 3; P-02 |
| Q2 | tarjeta nueva «Cuántos niños se midieron» (52 de 547, Ayaviri) al final de «Más contexto»; los enlaces de las 3 citas | X-02 (S-01); P-02 |
| Q3 | cifra nueva `gasto_ex_pan` 2024, Lima Metropolitana, contexto (S/ 260,7 millones); su tarjeta «Gasto en Lima Metropolitana en 2024»; su línea de cita; «Datos de: Gasto MEF 2024–2025»; los enlaces de las 6 citas | X-03 (R-03); P-02 |
| Q4 | solo los enlaces de las 10 citas | P-02 |

Ni cifras, ni semáforos, ni niveles de confianza de las cifras existentes cambian (`test_respuestas` compara todos los campos de cifra, el semáforo de la respuesta y la confianza con la referencia del slice 1).

### Regla de regresión: tarjetas por título

La tarjeta nueva de Q2 y la de Q3 no corren los índices de las demás: `indices_por_titulo` (en `tests/test_regresion_q1_q4.py`) alinea las tarjetas de `mas_contexto` con las de la referencia por título; las nuevas toman los índices siguientes. Prueba propia: `tests/test_s3_01_decisiones.py::test_tarjetas_nuevas_no_corren_los_indices_de_las_demas`. No se aprobó ninguna diferencia falsa.

## Rótulos a YAML

Los 8 rótulos de la historia (más «Cómo citar» y el texto del enlace, supuesto S3-01-d) están en `curados/motor/textos/capas.yaml` → `rotulos`. `ficha.markdown(res, rotulos=None)` los lee (`ficha.rotulos(raiz)`); la web leerá la misma tabla.

Comprobación de «idéntico byte a byte»: el `ficha.py` anterior (commit `6f6abba`, con los rótulos fijos) y el nuevo se aplican al mismo `respuesta.json` de Q1–Q4 (el de esta rama). Quitando el sufijo ` [Documento oficial](url)` de cada cita, que es el único cambio del `.md` que viene de los enlaces, los dos `.md` son iguales byte a byte:

```
q1 idéntico byte a byte (sin los enlaces nuevos): True | .md de la CLI == markdown():  True
q2 idéntico byte a byte (sin los enlaces nuevos): True | .md de la CLI == markdown():  True
q3 idéntico byte a byte (sin los enlaces nuevos): True | .md de la CLI == markdown():  True
q4 idéntico byte a byte (sin los enlaces nuevos): True | .md de la CLI == markdown():  True
```

Prueba permanente: `tests/test_s3_01_decisiones.py::test_rotulos_en_yaml_igual_a_los_de_antes`, `::test_ficha_no_fija_rotulos_en_el_codigo` y `::test_md_usa_los_rotulos_del_yaml` (con los rótulos de siempre pasados a mano el `.md` es idéntico byte a byte; con otros, cambia).

## Enlaces de las citas (P-02)

`capa3.citas` = `[{texto, url, id_cifra}]`, con las mismas líneas que `capa3.para_citar` (que no cambia). Con dorada, la `url` de `cifras_doradas.csv`; si no, `url_portal` (o `url_datos`) del catálogo de fuentes; sin enlace oficial, vacío. La respuesta de «no se puede» lleva `url` vacío. El `.md` agrega ` [Documento oficial](url)` al final de la cita.

### Q1
| # | cifra (indicador, año, territorio) | origen del enlace | url |
|---|---|---|---|
| 0 | endes_anemia_6_35m_oms2024, 2025, Huancavelica | cifras_doradas.csv (DOR-OMS-2025-09) | https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf |
| 1 | endes_anemia_6_35m, 2025, Huancavelica | cifras_doradas.csv (DOR-ANE-2025-09) | https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf |
| 2 | endes_anemia_6_35m, 2015, Huancavelica | catalogo_fuentes.csv | https://proyectos.inei.gob.pe/microdatos/ |
| 3 | endes_anemia_6_35m_oms2024, 2024, Huancavelica | cifras_doradas.csv (DOR-OMS-2024-09) | https://proyectos.inei.gob.pe/endes/2024/departamentales/Endes09/pdf/Cap09.pdf |

### Q2
| # | cifra (indicador, año, territorio) | origen del enlace | url |
|---|---|---|---|
| 0 | sien_anemia_tamizados_6_35m, 2025, Ayaviri | cifras_doradas.csv (DOR-SIEN-2025-210801) | https://cdn.www.gob.pe/uploads/document/file/9599740/7857855-indicadores-ninos-diciembre-2025-base-de-datos-hisminsa.xlsx |
| 1 | endes_anemia_6_35m_oms2024, 2025, Puno | cifras_doradas.csv (DOR-OMS-2025-21) | https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf |
| 2 | sien_cobertura_tamizaje_6_35m, 2025, Puno | catalogo_fuentes.csv | https://web.ins.gob.pe/es/alimentacion-y-nutricion/vigilancia-alimentaria-y-nutricional/sala-nutricional |

### Q3
| # | cifra (indicador, año, territorio) | origen del enlace | url |
|---|---|---|---|
| 0 | gasto_ex_pan, 2025, San Juan de Lurigancho | catalogo_fuentes.csv | https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto |
| 1 | gasto_ex_pan, 2025, Lima Metropolitana (provincia de Lima) | catalogo_fuentes.csv | https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto |
| 2 | sien_anemia_tamizados_6_35m, 2025, San Juan de Lurigancho | cifras_doradas.csv (DOR-SIEN-2025-150132) | https://cdn.www.gob.pe/uploads/document/file/9599740/7857855-indicadores-ninos-diciembre-2025-base-de-datos-hisminsa.xlsx |
| 3 | sien_cobertura_tamizaje_6_35m, 2025, Lima Metropolitana (provincia de Lima) | catalogo_fuentes.csv | https://web.ins.gob.pe/es/alimentacion-y-nutricion/vigilancia-alimentaria-y-nutricional/sala-nutricional |
| 4 | endes_anemia_6_35m_oms2024, 2025, Lima Metropolitana (provincia de Lima) | cifras_doradas.csv (DOR-OMS-2025-LM1501) | https://proyectos.inei.gob.pe/endes/2025/ppr/Informe_Indicadores_de_Resultados_de_los_Programas_Presupuestales_ENDES_2025.pdf |
| 5 | gasto_ex_pan, 2024, Lima Metropolitana (provincia de Lima) | catalogo_fuentes.csv | https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto |

### Q4
| # | cifra (indicador, año, territorio) | origen del enlace | url |
|---|---|---|---|
| 0 | mapa_pobreza_2018, 2018, Anguía | cifras_doradas.csv (DOR-MAPA-2018-060402) | https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1718/Libro.pdf |
| 1 | mapa_pobreza_2018, 2018, Oxamarca | cifras_doradas.csv (DOR-MAPA-2018-060308) | https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1718/Libro.pdf |
| 2 | mapa_pobreza_2018, 2018, Uchuraccay | cifras_doradas.csv (DOR-MAPA-2018-050410) | https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1718/Libro.pdf |
| 3 | enaho_pobreza_monetaria, 2025, Ayacucho | cifras_doradas.csv (DOR-POB-2025-05) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 4 | enaho_pobreza_monetaria, 2025, Cajamarca | cifras_doradas.csv (DOR-POB-2025-06) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 5 | enaho_pobreza_monetaria, 2025, Huancavelica | cifras_doradas.csv (DOR-POB-2025-09) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 6 | enaho_pobreza_monetaria, 2025, Huánuco | cifras_doradas.csv (DOR-POB-2025-10) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 7 | enaho_pobreza_monetaria, 2025, Loreto | cifras_doradas.csv (DOR-POB-2025-16) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 8 | enaho_pobreza_monetaria, 2025, Pasco | cifras_doradas.csv (DOR-POB-2025-19) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |
| 9 | enaho_pobreza_monetaria, 2025, Puno | cifras_doradas.csv (DOR-POB-2025-21) | https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025 |

## Vía estructurada de S2-00

`tests/test_cli_preguntar.py::test_via_estructurada_igual_a_la_base_de_s2_00` sigue comparando con `backlog/slice-2/evidencia/base_estructurada/` (que no se tocó). Para exceptuar solo lo aprobado, genera las respuestas con una raíz de trabajo cuyo `parametros_motor.yaml` vuelve al valor de antes de X-02, X-03 y X-04, y descarta del resultado el campo nuevo `capa3.citas` (P-02). Todo lo demás debe ser igual.
