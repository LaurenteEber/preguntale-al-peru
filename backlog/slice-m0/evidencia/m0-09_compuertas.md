# M0-09 — Compuertas de proporciones (evidencia)

**Fecha:** 9/11/2026 · **Código:** `src/pap/inferencia/compuertas.py` · **Pruebas:** `tests/inferencia/test_compuertas.py` (28 pruebas, rápidas)

## Qué hace
El árbol del diseño §15.1 y la confianza del §15.2 **sin lógica nueva**: llama a `r_enc_02`, `r_enc_03` y `r_enc_04` de
`src/pap/motor/validador/reglas_etapa4.py` (a través de `correr_regla`, `accion_final` y `estado_cifra`) con los parámetros de
`reglas/reglas.json` (`contexto_compuertas()` solo lee ese archivo). Devuelve `Compuerta(estado, motivos[], confianza, motivo_confianza, rotulo)`.
- Las que suprimen cortan el árbol; las referenciales se acumulan; gana la más severa (`accion_final`, orden de R-MOTOR-02); se guardan todos los motivos.
- Rótulo «menos de {límite superior}» o «más de {límite inferior}» cuando p = 0 o p = 1 (numerador = casos con y = 1; denominador = n).
- **Paso 8 (no respuesta del ítem): no se aplica** porque K-07 no está aprobada (`compuertas.paso_no_respuesta_activo: false`); la tasa solo se devuelve (`tasa_no_respuesta`).
- Dominio con n = 0 → `sin_datos`. Un dato que falta → `suprimida` con `metadato_faltante` (R-MOTOR-02).
- Confianza (§15.2): alta = verificada y coincide con su cifra oficial, sin referencial; media = verificada sin cifra oficial o plan compuesto, sin referencial; baja = cualquier referencial. Receta sin verificar y publicable: baja (supuesto M0-09).

## Una prueba por rama
| Paso §15.1 | Prueba |
|---|---|
| parámetros de reglas.json (y que un cambio ahí cambia el resultado) | `test_los_parametros_salen_de_reglas_json`, `test_cambiar_un_parametro_de_reglas_cambia_la_compuerta` |
| 1 R-ENC-02 n < 25 suprime y corta | `test_paso1_menos_de_25_casos_suprime_y_corta` |
| 2 R-ENC-02 25–49 referencial | `test_paso2_de_25_a_49_casos_es_referencial_y_sigue`, `test_bajo_50_casos_rige_solo_r_enc_02` |
| 3 R-ENC-04 suprime: n efectivo < 30 / ancho ≥ 30 pp / ancho relativo > 130 % con ancho > 5 pp (y su límite) | `test_paso3_*` (4) |
| 4 R-ENC-04 referencial: ancho relativo > 59 %, n efectivo < 50, gl < 8, CV ref > 15 % (L9); p entre 10 % y 90 % no pasa | `test_paso4_*` (5) |
| 5 rótulo p = 0 y p = 1; el rótulo se acumula con un referencial | `test_paso5_*` (3), `test_el_rotulo_se_acumula_a_los_motivos_referenciales` |
| 6 R-ENC-03 CV > 30 % suprime (30 % exacto no) | `test_paso6_cv_mayor_de_30_por_ciento_suprime` |
| 7 R-ENC-03 15–30 % o gl < 8 referencial (15 % exacto se publica); CV ref con mín(p, 1−p) | `test_paso7_*` (2), `test_el_cv_de_referencia_usa_el_menor_entre_p_y_1_menos_p` |
| 8 no respuesta: sin efecto | `test_paso8_la_no_respuesta_no_cambia_el_estado_porque_k07_no_esta_aprobada` |
| sin datos / dato que falta | `test_dominio_vacio_es_sin_datos`, `test_un_dato_que_falta_suprime_por_metadato_faltante` |
| §15.2 confianza | `test_confianza_alta_media_y_baja` |
| adaptador + compuertas sobre el sintético | `test_las_compuertas_sobre_el_sintetico_dan_el_estado_que_describe_cada_dominio` |

## Las 90 filas del cubo 2024 (criterio 4)
`test_las_90_filas_del_cubo_dan_el_mismo_estado_que_el_oraculo_de_m0_00` alimenta `evidencia/m0-00_filas_cubo_2024.csv` (valores del cubo, metadatos de
`dim_indicador.yaml`) a `compuertas.evaluar_cifra` y lo compara fila por fila con `evidencia/m0-00_estados_cubo.csv` (calculado con `reglas_etapa4.py`):
- **Estado:** igual en las 90 filas → **85 publicables y 5 referenciales** (las 5 de DCI por R-ENC-04: Lima Región y los departamentos 04, 17, 18 y 23).
- **Acción final:** igual en las 90.
- **Reglas disparadas** (`regla:acción:motivo`): iguales en las 90.
- **Diferencias:** ninguna (no hay consulta tipo C por este criterio).

Las compuertas no leen el cubo: la prueba usa el CSV de filas ya guardado. El hash del cubo sigue empezando en `010ea965` (sha256 `010ea965381c…`).
