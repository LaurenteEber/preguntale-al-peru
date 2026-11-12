# M0-02 — Tamaño de los ZIP de la ENDES 2024 (medido el 9/11/2026)

Tamaño = bytes del archivo bajado de `proyectos.inei.gob.pe` (Stata), igual al `bytes` de su `datapackage.json`. 1629 y 1638 son los ya registrados (no se bajaron de nuevo).

| Módulo | Recurso | Bytes | MB |
|---|---|---:|---:|
| 1629 | endes-2024-hogar | 5,614,967 | 5.6 |
| 1630 | endes-2024-vivienda | 3,658,861 | 3.7 |
| 1631 | endes-2024-datos-basicos-mef | 9,651,011 | 9.7 |
| 1632 | endes-2024-historia-nacimiento | 7,938,516 | 7.9 |
| 1633 | endes-2024-embarazo-parto | 5,854,080 | 5.9 |
| 1634 | endes-2024-inmunizacion-salud | 12,107,078 | 12.1 |
| 1635 | endes-2024-nupcialidad-fecundidad | 5,881,052 | 5.9 |
| 1636 | endes-2024-sida-condon | 7,162,518 | 7.2 |
| 1637 | endes-2024-mortalidad-materna-violencia | 6,287,710 | 6.3 |
| 1638 | endes-2024-anemia | 9,463,248 | 9.5 |
| 1639 | endes-2024-disciplina-infantil | 4,277,216 | 4.3 |
| 1640 | endes-2024-salud | 7,067,246 | 7.1 |
| 1641 | endes-2024-programas-sociales | 3,066,353 | 3.1 |
| **Total 13 ZIP** | | **88,029,856** | **88.0** |

| Documento (PDF) | Recurso | Bytes | MB |
|---|---|---:|---:|
| | endes-2024-ficha-tecnica | 706,542 | 0.7 |
| | endes-2024-cuestionario-hogar | 1,701,758 | 1.7 |
| | endes-2024-cuestionario-individual | 7,079,549 | 7.1 |
| | endes-2024-cuestionario-salud | 1,913,248 | 1.9 |
| | endes-2024-diccionario-hogar | 787,877 | 0.8 |
| | endes-2024-diccionario-individual | 3,901,724 | 3.9 |
| | endes-2024-diccionario-salud | 690,491 | 0.7 |
| **Total 7 PDF** | | **16,781,189** | **16.8** |

**Bloque 2024 (ZIP + PDF): 104,811,045 bytes = 104.8 MB.** Archivo más grande: 1634 con 12,1 MB; ninguno se acerca a 2 GiB, así que `split` no se usa.

## Proyección a 2015–2025

**Método.** Hay registrados el módulo de hogar y el de anemia de cada año 2015–2025 (SPSS en 2015–2020, Stata desde 2021; K-06). Para cada año se escala el bloque 2024 de 13 ZIP por la razón (hogar + anemia del año) / (hogar + anemia de 2024 = 15,078,215 bytes). Es una estimación gruesa: supone que los demás módulos crecen igual que esos dos y que cada año tiene los 13 módulos (los años anteriores pueden tener menos, así que es más bien un techo). No incluye PDF (≈16.8 MB por año como mucho).

| Año | Hogar + anemia (bytes) | Bloque estimado (MB) |
|---|---:|---:|
| 2015 | 11,622,821 | 67.9 |
| 2016 | 11,180,989 | 65.3 |
| 2017 | 11,233,841 | 65.6 |
| 2018 | 16,278,301 | 95.0 |
| 2019 | 14,366,263 | 83.9 |
| 2020 | 12,743,940 | 74.4 |
| 2021 | 14,759,579 | 86.2 |
| 2022 | 13,989,547 | 81.7 |
| 2023 | 18,727,088 | 109.3 |
| 2024 | 15,078,215 | 88.0 |
| 2025 | 15,197,666 | 88.7 |
| **Total 2015–2025** | | **906.0** |

Con PDF de cada año al nivel de 2024 (techo): ≈ 1090.6 MB ≈ 1.09 GB, muy por debajo del límite de 1 000 archivos por release (≈ 20 archivos por año) y del umbral `almacen.espacio_libre_min_gb` (50 GB) del disco; el crudo descomprimido es otra cosa y se mide en M0-04.
