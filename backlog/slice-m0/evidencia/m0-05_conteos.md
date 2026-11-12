# M0-05 — Conteos del índice de variables de la ENDES 2024

Medido el 9/11/2026 en el Mac del dueño con `uv run pap variables indexar --encuesta ENDES --anio 2024` (34 DTA de los 13 ZIP registrados, `pyreadstat` 1.3.7 con `metadataonly=True` y `user_missing=True`, sin tope de etiquetas, en el subproceso aislado de M0-04). Salida: `biblioteca/variables/{archivos,variables,categorias}.parquet` (no van a git: `biblioteca/**/*.parquet`). Reproducir: `uv run pytest -q -m regresion_microdatos tests/inferencia/test_indice_regresion.py`.

## Filas del índice

| Tabla | Filas |
|---|---:|
| `archivos.parquet` | 34 |
| `variables.parquet` | 2,856 |
| `categorias.parquet` | 7,602 |

- Las 2,856 variables son exactamente las columnas de los 34 Parquet de M0-04 menos `anio` (incluye 16 HHID derivados de CASEID). Todas en estado `propuesto`.
- Clases (de `clases_columnas.yaml`): diseno 18, geo 4, llave 60, peso 4; sin clase 2,770 (las pone M1).

## Textos de etiqueta distintos y tokens por texto

- Textos de etiqueta **distintos** (variables y categorías, `etiqueta_curada`, sin vacíos): **4,129** (originales distintos: 4,148).
- «Tokens» por texto, **aproximados por palabras** (separadas por espacio; el tokenizer de e5-small es de M1 y aún no está disponible): **p50 = 5**, **p95 = 14**, máximo 20. Por caracteres: p50 = 32, p95 = 80, máximo 80.
- Nota: 328 etiquetas de variable miden exactamente 80 caracteres (el tope de Stata); varias están cortadas («…con ese mét»). Quedan marcadas con el control `etiqueta_posible_corte`; el texto completo está en los cuestionarios (M1).

## Variables por archivo

| Archivo | ZIP | Unidad | Filas | Variables | Categorías |
|---|---|---|---:|---:|---:|
| CSALUD01 | 968-Modulo1640.zip | hogar | 34,018 | 258 | 648 |
| CSALUD08 | 968-Modulo1640.zip | persona_del_hogar | 41,309 | 53 | 163 |
| DIT | 968-Modulo1634.zip | hijo_de_mujer | 19,245 | 64 | 196 |
| PS_BECA18 | 968-Modulo1641.zip | persona_del_hogar | 48 | 10 | 4 |
| PS_COMEDOR | 968-Modulo1641.zip | persona_del_hogar | 1,437 | 10 | 4 |
| PS_PENSION65 | 968-Modulo1641.zip | persona_del_hogar | 2,745 | 10 | 4 |
| PS_QALIWARMA | 968-Modulo1641.zip | persona_del_hogar | 18,984 | 11 | 7 |
| PS_TRABAJA | 968-Modulo1641.zip | persona_del_hogar | 78 | 10 | 4 |
| PS_VL | 968-Modulo1641.zip | persona_del_hogar | 9,824 | 10 | 4 |
| PS_WAWAWASI | 968-Modulo1641.zip | persona_del_hogar | 725 | 10 | 4 |
| Programas_Sociales_x_Hogar | 968-Modulo1641.zip | hogar | 34,018 | 20 | 40 |
| RE223132 | 968-Modulo1632.zip | mujer | 34,252 | 150 | 507 |
| RE516171 | 968-Modulo1635.zip | mujer | 34,252 | 85 | 436 |
| RE758081 | 968-Modulo1636.zip | mujer | 34,252 | 199 | 514 |
| REC0111 | 968-Modulo1631.zip | mujer | 37,117 | 104 | 366 |
| REC21 | 968-Modulo1632.zip | hijo_de_mujer | 60,693 | 35 | 52 |
| REC41 | 968-Modulo1633.zip | hijo_de_mujer | 19,751 | 148 | 405 |
| REC42 | 968-Modulo1634.zip | mujer | 34,252 | 170 | 416 |
| REC43 | 968-Modulo1634.zip | hijo_de_mujer | 19,751 | 169 | 460 |
| REC44 | 968-Modulo1638.zip | hijo_de_mujer | 19,751 | 35 | 52 |
| REC82 | 968-Modulo1636.zip | columna_de_calendario | 171,260 | 5 | 5 |
| REC83 | 968-Modulo1637.zip | hermano_de_mujer | 141,805 | 20 | 43 |
| REC84DV | 968-Modulo1637.zip | mujer | 34,252 | 221 | 623 |
| REC91 | 968-Modulo1631.zip | mujer | 37,117 | 344 | 913 |
| REC93DVdisciplina | 968-Modulo1639.zip | hijo_de_mujer | 15,462 | 19 | 30 |
| REC94 | 968-Modulo1633.zip | hijo_de_mujer | 19,751 | 62 | 193 |
| REC95 | 968-Modulo1634.zip | hijo_de_mujer | 19,751 | 301 | 691 |
| RECH0 | 968-Modulo1629.zip | hogar | 37,390 | 44 | 76 |
| RECH1 | 968-Modulo1629.zip | persona_del_hogar | 135,045 | 36 | 90 |
| RECH23 | 968-Modulo1630.zip | hogar | 37,390 | 130 | 423 |
| RECH4 | 968-Modulo1629.zip | persona_del_hogar | 135,045 | 22 | 61 |
| RECH5 | 968-Modulo1638.zip | persona_del_hogar | 38,488 | 40 | 77 |
| RECH6 | 968-Modulo1638.zip | persona_del_hogar | 20,290 | 43 | 72 |
| RECHM | 968-Modulo1629.zip | persona_del_hogar | 3,002 | 8 | 19 |
| **Total** | | | | **2,856** | **7,602** |

## Códigos especiales propuestos (`es_especial = propuesto`)

- **1,082** códigos en 1,017 variables; origen: etiqueta 1082.
- **Declarados por el archivo: 0.** Los 34 archivos son Stata (K-06) y ninguno trae perdidos extendidos (.a–.z) ni `missing_ranges`; el manifiesto de M0-04 tampoco trae `perdidos`. Todos los propuestos salen de la etiqueta («no sabe», «no responde», «no aplica») o de un código 98/99/998/999/9996–9999 con etiqueta.
- Frecuencia medida en el Parquet para todos: 592 con filas, 490 con 0 filas (el código está etiquetado pero no aparece en 2024).
- Los nombres de las columnas que más códigos propuestos tienen: REC44.HW71 (3), RECH6.HC70 (3), RECH6.HC71 (3).

## Controles de §7.3 corridos en 2024

| Control | Variables | Categorías | Resultado |
|---|---:|---:|---|
| `etiqueta_vacia` | 2 | 1 | 2 variables sin etiqueta en el archivo (`RECH0.LATITUDY`, `RECH0.LONGITUDX`) y 1 categoría con etiqueta vacía (`RECH6.HC33=5`) |
| `mojibake_reparado` | 0 | 0 | ninguna etiqueta necesitó reparación de codificación |
| `mojibake_sin_reparar` | 0 | 0 | **0** |
| `etiqueta_acento_grave` | 66 | 8 | erratas del INEI («querìa», «màs», «sòlida»); no es mojibake; se marcan, no se corrigen solas |
| `etiqueta_posible_corte` | 328 | 0 | etiquetas de variable de 80 caracteres |
| `especial_declarado_sin_filas` | 0 | 0 | ninguno declarado en 2024 |
| frecuencia de códigos especiales | — | — | contada para los 1,082 propuestos (columnas `frecuencia` y `proporcion_filas` de `categorias.parquet`); la comparación entre años queda programada (`control_frecuencia_entre_anios`) y probada con datos sintéticos, se usa desde M1/M2 |
| universo contra los datos (99,5 %) y etiqueta distinta entre años | — | — | programados y probados con datos sintéticos (`control_universo`, `coincidencia_universo_parquet`, `control_etiquetas_entre_anios`); se usan desde M1 y M2 |

## Uniones declaradas: filas antes y después

Cada unión es hijo → padre (unión izquierda). «Antes» = filas del hijo; «después» = filas tras la unión; «con pareja» = filas del hijo que encontraron al padre (unión interna); «llaves repetidas» = filas de más del padre en las columnas de la unión. Sin pérdida ni duplicación: antes = después = con pareja y 0 repetidas. Fuente: `curados/inferencia/archivos_endes_2024.yaml`; prueba: `test_uniones_declaradas_sin_perdida_ni_duplicacion`.

| Hijo → Padre | Por | Antes | Después | Con pareja | Repetidas | OK |
|---|---|---:|---:|---:|---:|:-:|
| RECH1 → RECH0 | HHID | 135,045 | 135,045 | 135,045 | 0 | sí |
| RECH23 → RECH0 | HHID | 37,390 | 37,390 | 37,390 | 0 | sí |
| RECH4 → RECH0 | HHID | 135,045 | 135,045 | 135,045 | 0 | sí |
| RECH5 → RECH0 | HHID | 38,488 | 38,488 | 38,488 | 0 | sí |
| RECH6 → RECH0 | HHID | 20,290 | 20,290 | 20,290 | 0 | sí |
| RECHM → RECH0 | HHID | 3,002 | 3,002 | 3,002 | 0 | sí |
| CSALUD01 → RECH0 | HHID | 34,018 | 34,018 | 34,018 | 0 | sí |
| CSALUD08 → RECH0 | HHID | 41,309 | 41,309 | 41,309 | 0 | sí |
| Programas_Sociales_x_Hogar → RECH0 | HHID | 34,018 | 34,018 | 34,018 | 0 | sí |
| PS_BECA18 → RECH0 | HHID | 48 | 48 | 48 | 0 | sí |
| PS_COMEDOR → RECH0 | HHID | 1,437 | 1,437 | 1,437 | 0 | sí |
| PS_PENSION65 → RECH0 | HHID | 2,745 | 2,745 | 2,745 | 0 | sí |
| PS_QALIWARMA → RECH0 | HHID | 18,984 | 18,984 | 18,984 | 0 | sí |
| PS_TRABAJA → RECH0 | HHID | 78 | 78 | 78 | 0 | sí |
| PS_VL → RECH0 | HHID | 9,824 | 9,824 | 9,824 | 0 | sí |
| PS_WAWAWASI → RECH0 | HHID | 725 | 725 | 725 | 0 | sí |
| REC0111 → RECH0 | HHID | 37,117 | 37,117 | 37,117 | 0 | sí |
| REC93DVdisciplina → RECH0 | HHID | 15,462 | 15,462 | 15,462 | 0 | sí |
| RECH6 → RECH1 | HHID, HC0=HVIDX | 20,290 | 20,290 | 20,290 | 0 | sí |
| PS_BECA18 → RECH1 | HHID, HVIDX | 48 | 48 | 48 | 0 | sí |
| PS_COMEDOR → RECH1 | HHID, HVIDX | 1,437 | 1,437 | 1,437 | 0 | sí |
| PS_PENSION65 → RECH1 | HHID, HVIDX | 2,745 | 2,745 | 2,745 | 0 | sí |
| PS_QALIWARMA → RECH1 | HHID, HVIDX | 18,984 | 18,984 | 18,984 | 0 | sí |
| PS_TRABAJA → RECH1 | HHID, HVIDX | 78 | 78 | 78 | 0 | sí |
| PS_VL → RECH1 | HHID, HVIDX | 9,824 | 9,824 | 9,824 | 0 | sí |
| PS_WAWAWASI → RECH1 | HHID, HVIDX | 725 | 725 | 725 | 0 | sí |
| CSALUD08 → RECH1 | HHID, QS801=HVIDX | 41,309 | 41,309 | 41,309 | 0 | sí |
| CSALUD08 → CSALUD01 | HHID | 41,309 | 41,309 | 41,309 | 0 | sí |
| REC0111 → RECH1 | HHID, V003=HVIDX | 37,117 | 37,117 | 37,117 | 0 | sí |
| REC21 → REC0111 | CASEID | 60,693 | 60,693 | 60,693 | 0 | sí |
| REC41 → REC0111 | CASEID | 19,751 | 19,751 | 19,751 | 0 | sí |
| REC42 → REC0111 | CASEID | 34,252 | 34,252 | 34,252 | 0 | sí |
| REC43 → REC0111 | CASEID | 19,751 | 19,751 | 19,751 | 0 | sí |
| REC44 → REC0111 | CASEID | 19,751 | 19,751 | 19,751 | 0 | sí |
| REC82 → REC0111 | CASEID | 171,260 | 171,260 | 171,260 | 0 | sí |
| REC83 → REC0111 | CASEID | 141,805 | 141,805 | 141,805 | 0 | sí |
| REC84DV → REC0111 | CASEID | 34,252 | 34,252 | 34,252 | 0 | sí |
| REC91 → REC0111 | CASEID | 37,117 | 37,117 | 37,117 | 0 | sí |
| REC94 → REC0111 | CASEID | 19,751 | 19,751 | 19,751 | 0 | sí |
| REC95 → REC0111 | CASEID | 19,751 | 19,751 | 19,751 | 0 | sí |
| RE223132 → REC0111 | CASEID | 34,252 | 34,252 | 34,252 | 0 | sí |
| RE516171 → REC0111 | CASEID | 34,252 | 34,252 | 34,252 | 0 | sí |
| RE758081 → REC0111 | CASEID | 34,252 | 34,252 | 34,252 | 0 | sí |
| DIT → REC0111 | CASEID | 19,245 | 19,245 | 19,245 | 0 | sí |

44 uniones; 44 sin pérdida ni duplicación.

**No declarada:** REC93DVdisciplina → REC0111 por CASEID: 15,462 filas del hijo, 15,121 con pareja; **341 sin la mujer en REC0111** (consulta C-M0-05-2). Sí se une a RECH0 por HHID sin pérdida.

## Pendiente de re-conversión (M0-04)

Al completar `clases_columnas.yaml`, 11 archivos cambiarían el tipo de unas columnas de diseño al convertir de nuevo (REC0111: V001, V021, V022, V024, V025; los 10 archivos con QHCLUSTER: CSALUD01, CSALUD08, Programas_Sociales_x_Hogar y 7 PS_*), de DOUBLE a INTEGER. Se probó convirtiendo los 34 archivos a una carpeta temporal: **la `huella_contenido_v1` de los 34 sale idéntica** (los valores no cambian), solo cambia el tipo declarado. Los Parquet y el `manifiesto.json` que hay hoy se hicieron con las clases provisionales; correr `uv run pap microdatos convertir --encuesta ENDES --anio 2024` los deja al día (el índice y sus pruebas no dependen de ese tipo).
