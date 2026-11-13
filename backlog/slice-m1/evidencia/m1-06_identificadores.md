# M1-06 tarea 5 — Documento n.º 11 «Identificadores de las bases de datos» frente a las llaves declaradas

Generado por `m1-06_identificadores.py`. Documento: recurso `endes-2024-identificadores-bd` (`2024-5-Ident-de-las-bd.pdf`, sha256 `8d5927891982d409…`), leído con `pdftotext`. Tiene 2 páginas: la tabla de 34 filas (identificador principal y hasta dos alternos) y las «Precisiones».

## Llaves

| Fila | Tabla | Identificador principal (documento) | Llave declarada | ¿Coincide? | Filas | Filas con la llave completa | Llaves distintas | Alternos del documento |
|---|---|---|---|---|---|---|---|---|
| 1 | RECH0 | HHID | HHID | sí | 37,390 | 37,390 | 37,390 | — |
| 3 | RECH1 | HHID + HVIDX | HHID + HVIDX | sí | 135,045 | 135,045 | 135,045 | — |
| 5 | RECH23 | HHID | HHID | sí | 37,390 | 37,390 | 37,390 | — |
| 4 | RECH4 | HHID + IDXH4 | HHID + IDXH4 | sí | 135,045 | 135,045 | 135,045 | — |
| 6 | RECH5 | HHID + HA0 | HHID + HA0 | sí | 38,488 | 38,488 | 38,488 | — |
| 7 | RECH6 | HHID + HC0 | HHID + HC0 | sí | 20,290 | 20,290 | 20,290 | — |
| 2 | RECHM | HHID + NRO_ORDEN_ID | HHID + NRO_ORDEN_ID | sí | 3,002 | 3,002 | 3,002 | — |
| 33 | CSALUD01 | HHID + QSNUMERO | HHID | **NO** | 34,018 | 34,018 | 34,018 | — |
| 34 | CSALUD08 | HHID + QS801 | HHID + QS801 | sí | 41,309 | 41,309 | 41,309 | — |
| 8 | Programas_Sociales_x_Hogar | HHID | HHID | sí | 34,018 | 34,018 | 34,018 | — |
| 9 | PS_BECA18 | HHID + HVIDX | HHID + HVIDX | sí | 48 | 48 | 48 | — |
| 10 | PS_COMEDOR | HHID + HVIDX | HHID + HVIDX | sí | 1,437 | 1,437 | 1,437 | — |
| 11 | PS_PENSION65 | HHID + HVIDX | HHID + HVIDX | sí | 2,745 | 2,745 | 2,745 | — |
| 12 | PS_QALIWARMA | HHID + HVIDX | HHID + HVIDX | sí | 18,984 | 18,984 | 18,984 | — |
| 15 | PS_TRABAJA | HHID + HVIDX | HHID + HVIDX | sí | 78 | 78 | 78 | — |
| 14 | PS_VL | HHID + HVIDX | HHID + HVIDX | sí | 9,824 | 9,824 | 9,824 | — |
| 13 | PS_WAWAWASI | HHID + HVIDX | HHID + HVIDX | sí | 725 | 725 | 725 | — |
| 16 | REC0111 | CASEID | CASEID | sí | 37,117 | 37,117 | 37,117 | — |
| 17 | REC21 | CASEID + BIDX | CASEID + BIDX | sí | 60,693 | 60,693 | 60,693 | CASEID + BORD; CASEID + B16 |
| 19 | REC41 | CASEID + MIDX | CASEID + MIDX | sí | 19,751 | 19,751 | 19,751 | — |
| 20 | REC42 | CASEID | CASEID | sí | 34,252 | 34,252 | 34,252 | — |
| 21 | REC43 | CASEID + HIDX | CASEID + HIDX | sí | 19,751 | 19,751 | 19,751 | — |
| 22 | REC44 | CASEID + HWIDX | CASEID + HWIDX | sí | 19,751 | 19,751 | 19,751 | — |
| 25 | REC82 | CASEID + VCOL | CASEID + VCOL | sí | 171,260 | 171,260 | 171,260 | — |
| 26 | REC83 | CASEID + MMIDX | CASEID + MMIDX | sí | 141,805 | 141,805 | 141,805 | — |
| 27 | REC84DV | CASEID | CASEID | sí | 34,252 | 34,252 | 34,252 | — |
| 28 | REC91 | CASEID | CASEID | sí | 37,117 | 37,117 | 37,117 | — |
| 29 | REC93DVdisciplina | CASEID + QCOL93 | CASEID + QCOL93 | sí | 15,462 | 15,462 | 15,462 | CASEID + Q1035NO |
| 30 | REC94 | CASEID + IDX94 | CASEID + IDX94 | sí | 19,751 | 19,751 | 19,751 | — |
| 31 | REC95 | CASEID + IDX95 | CASEID + IDX95 | sí | 19,751 | 19,751 | 19,751 | CASEID + Q452 |
| 18 | RE223132 | CASEID | CASEID | sí | 34,252 | 34,252 | 34,252 | — |
| 23 | RE516171 | CASEID | CASEID | sí | 34,252 | 34,252 | 34,252 | — |
| 24 | RE758081 | CASEID | CASEID | sí | 34,252 | 34,252 | 34,252 | — |
| 32 | DIT | CASEID + BIDX | CASEID + BIDX | sí | 19,245 | 19,245 | 19,245 | CASEID + BORD |

## Llaves alternas del documento comprobadas en los datos

| Tabla | Alterna | Filas | Llaves distintas |
|---|---|---|---|
| REC21 | CASEID + BORD | 60,693 | 60,693 distintas en 60,693 con llave completa (0 filas con algún nulo) |
| REC21 | CASEID + B16 | 60,693 | 55,266 distintas en 59,142 con llave completa (1,551 filas con algún nulo) |
| DIT | CASEID + BORD | 19,245 | 19,245 distintas en 19,245 con llave completa (0 filas con algún nulo) |
| REC95 | CASEID + Q452 | 19,751 | 19,751 distintas en 19,751 con llave completa (0 filas con algún nulo) |
| REC93DVdisciplina | CASEID + Q1035NO | 15,462 | 15,462 distintas en 15,462 con llave completa (0 filas con algún nulo) |
| CSALUD01 | HHID + QSNUMERO | 34,018 | 34,018 distintas en 34,018 con llave completa (0 filas con algún nulo) |

## Uniones declaradas y lo que el documento dice

| Unión (hijo → padre) | Por | Cardinalidad | Respaldo |
|---|---|---|---|
| RECH1 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| RECH23 → RECH0 | HHID = HHID | 1:1 | doc11_hhid |
| RECH4 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| RECH5 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| RECH6 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| RECHM → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| CSALUD01 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| CSALUD08 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| Programas_Sociales_x_Hogar → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_BECA18 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_COMEDOR → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_PENSION65 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_QALIWARMA → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_TRABAJA → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_VL → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| PS_WAWAWASI → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| REC0111 → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| REC93DVdisciplina → RECH0 | HHID = HHID | n:1 | doc11_hhid |
| RECH6 → RECH1 | HHID = HHID, HC0 = HVIDX | n:1 | doc11_hvidx |
| PS_BECA18 → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_COMEDOR → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_PENSION65 → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_QALIWARMA → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_TRABAJA → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_VL → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| PS_WAWAWASI → RECH1 | HHID = HHID, HVIDX = HVIDX | n:1 | doc11_hvidx |
| CSALUD08 → RECH1 | HHID = HHID, QS801 = HVIDX | n:1 | doc11_hvidx |
| CSALUD08 → CSALUD01 | HHID = HHID | n:1 | doc11_hhid |
| REC0111 → RECH1 | HHID = HHID, V003 = HVIDX | n:1 | solo_datos |
| REC21 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC41 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC42 → REC0111 | CASEID = CASEID | 1:0..1 | doc11_caseid |
| REC43 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC44 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC82 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC83 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC84DV → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC91 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC94 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| REC95 → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |
| RE223132 → REC0111 | CASEID = CASEID | 1:0..1 | doc11_caseid |
| RE516171 → REC0111 | CASEID = CASEID | 1:0..1 | doc11_caseid |
| RE758081 → REC0111 | CASEID = CASEID | 1:0..1 | doc11_caseid |
| DIT → REC0111 | CASEID = CASEID | n:1 | doc11_caseid |

## Equivalencias de las «Precisiones»

- HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801 (número de línea de la persona en el hogar). Respalda RECH6 → RECH1 (HC0 = HVIDX), CSALUD08 → RECH1 (QS801 = HVIDX) y los PS_* → RECH1 (HVIDX = HVIDX).
- BIDX = MIDX = HIDX = HWIDX = IDX94 = IDX95 = QCOL93 (índice del hijo nacido vivo, empezando por el último); BORD = Q1035NO = Q452 (orden del nacimiento).
- «Si B16 = 0, es porque no fue listado en el hogar»: por eso B16 no puede ser llave (se repite el 0).

## Resultado

- 33 de 34 tablas con la llave igual a la del documento.
- **CSALUD01**: el documento da `HHID + QSNUMERO` y se declara `HHID`.
