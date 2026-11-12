# M1-00 — Documentos nuevos de la ENDES (tareas 4, 5 y 6)

12/11/2026, Mac. Solo `https://proyectos.inei.gob.pe`.

## Listado oficial «Consulta por Documentos»

Fuente: portal de microdatos del INEI, `Consulta_por_Documentos.asp` → `CambiaPeriodoDoc.asp` (POST, encuesta «Encuesta Demográfica y de Salud Familiar - ENDES», año 2024, periodo 5). Cada fila da el código de encuesta 968, el código del documento y el nombre del archivo que abre `VerFicha` (`DocumentosMetodologicos/2024-5/<archivo>.pdf`).

| Código | Documento | Archivo | En el proyecto |
|---|---|---|---|
| 1 | Cuestionario del Hogar | `CuestionarioHogar` | M0-02 |
| 2 | Cuestionario Individual | `CuestionarioIndividual` | M0-02 |
| 3 | Cuestionario de Salud | `CuestionarioSalud` | M0-02 |
| 4 | Diccionario Hogar | `DiccionarioHogar` | M0-02 |
| 5 | Diccionario Individual | `DiccionarioIndividual` | M0-02 |
| 6 | Diccionario Salud | `DiccionarioSalud` | M0-02 |
| 7 | Ficha técnica | `FichaTecnica` | M0-02 |
| 8 | Manual de la Entrevistadora | `ManualEntrevistadora` | **M1-00** |
| 9 | Manual del Antropometrista | `ManualAntropometrista` | **M1-00** |
| 10 | Manual de la Supervisora Local | `ManualSupervisoraLocal` | no se baja (decisión del dueño) |
| 11 | Identificadores de las bases de datos | `Ident-de-las-bd` (en la URL: `Ident%2Dde%2Dlas%2Dbd`) | **M1-00** |

## Descargas

Con `curl -f`, cada archivo en una carpeta nueva y vacía; el tamaño coincide con el `Content-Length` del servidor y todos empiezan con `%PDF-`.

| Recurso | URL exacta (`download_url`) | Bytes | SHA-256 |
|---|---|---|---|
| `endes-2024-manual-entrevistadora` | `…/Descarga/DocumentosMetodologicos/2024-5/ManualEntrevistadora.pdf` | 51 110 121 | `47a1c3d494339cb095d0d420698b2e61f0a4a34d5825cc22e09697c0212cd2d6` |
| `endes-2024-manual-antropometrista` | `…/Descarga/DocumentosMetodologicos/2024-5/ManualAntropometrista.pdf` | 15 754 430 | `7fc9ad4249b9217a283f7eabf22ac7b057426371474e18d17338b073f2ad84d3` |
| `endes-2024-identificadores-bd` | `…/Descarga/DocumentosMetodologicos/2024-5/Ident-de-las-bd.pdf` | 757 234 | `8d5927891982d4094673a63629d0f27100eef29ffce9791552787741fbc21b14` |
| `endes-2025-ficha-tecnica` | `…/Descarga/FichaTecnica/1038-Ficha.pdf` (`url_ficha` del catálogo, encuesta 1038) | 642 437 | `4e6c9a2c4ea5bd36517bf7d696c56d608c566bdc85f88aed85f1922f39ccb8ed` |

`…` = `https://proyectos.inei.gob.pe/iinei/srienaho`. Total 67,9 MB: dentro del tope de F-04 (C-M0-11-1: 2 GB en el Mac, 1,5 GB en el repo privado).

## Ficha técnica de la ENDES 2025 contra el informe (hojas 134 y 138)

Comparación palabra por palabra con `pdftotext -layout` de la ficha y de `biblioteca/cruda/bandeja/validacion_doradas/pap_endes2025_ppr.pdf`.

- **§IV «Muestras paneles con rotación»:** igual. Coinciden 250 de 259 palabras; lo distinto es el pie de página del informe («136 Perú: Indicadores de Resultados de los Programas Presupuestales») y el lugar del título de la figura n.º 1.
- **§3.1 «Antecedentes»:** la frase que cita C-M0-06-1 es idéntica en los dos: «Los conglomerados que tienen la misma numeración en la variable HV001 (conglomerado) en los años 2024 y 2025 son paneles.» Las demás viñetas coinciden salvo la del trabajo de campo: la ficha la actualiza («Desde el año 2019, el trabajo de campo se desarrolla regularmente entre enero y diciembre») y agrega que 165 conglomerados de 2025 se recuperaron hasta febrero de 2026 (5,1 % de la muestra anual), con 36 750 viviendas y 3 253 conglomerados ejecutados. El informe trae el texto anterior («Los meses de trabajo de campo de la encuesta ha variado…»).
- **Conclusión:** la cita de C-M0-06-1 (§3.1 y §IV) se sostiene con la ficha registrada. La diferencia del trabajo de campo no cambia ninguna cifra ni regla; queda como nota.

## Registro (12/11/2026)

Un `pap registrar INEI-ENDES <archivo> --recurso … --url-descarga …` por archivo (copia, sin `--mover`; los PDF originales quedan en `/tmp/pap-m1/descargas/`). Antes de registrar se comprobó que el SHA-256 de cada archivo coincide con el de la tabla «Descargas». El informe se registró sin `--url-descarga` (no hay URL oficial conocida; supuesto M1-00-s1 en `consultas_al_dueno.md`) y se **copió** desde `bandeja/validacion_doradas/`, cuyo `SHA256SUMS` sigue válido (`shasum -a 256 -c`, todos «OK»).

| Captura (`biblioteca/cruda/capturas/INEI-ENDES/…`) | Recurso | SHA-256 | Bytes | `download_url` |
|---|---|---|---|---|
| `2026-11-12` | `endes-2024-manual-entrevistadora` | `47a1c3d494339cb095d0d420698b2e61f0a4a34d5825cc22e09697c0212cd2d6` | 51 110 121 | `https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2024-5/ManualEntrevistadora.pdf` |
| `2026-11-12-2` | `endes-2024-manual-antropometrista` | `7fc9ad4249b9217a283f7eabf22ac7b057426371474e18d17338b073f2ad84d3` | 15 754 430 | `…/DocumentosMetodologicos/2024-5/ManualAntropometrista.pdf` |
| `2026-11-12-3` | `endes-2024-identificadores-bd` | `8d5927891982d4094673a63629d0f27100eef29ffce9791552787741fbc21b14` | 757 234 | `…/DocumentosMetodologicos/2024-5/Ident-de-las-bd.pdf` |
| `2026-11-12-4` | `endes-2025-ficha-tecnica` | `4e6c9a2c4ea5bd36517bf7d696c56d608c566bdc85f88aed85f1922f39ccb8ed` | 642 437 | `https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/1038-Ficha.pdf` |
| `2026-11-12-5` | `endes-2024-informe-ppr` | `c40ffb3fa0b98bb41b831c47a991968693ead5f787c61ad842e588762a1adf59` | 21 946 434 | — (sin URL oficial conocida) |

Todas las capturas nuevas guardan `access_url` = `https://proyectos.inei.gob.pe/microdatos/`, `source_id` INEI-ENDES, hash y bytes. `pap verificar INEI-ENDES`: «Recetas: 1 · capturas: 45 · archivos: 45 — Todo en orden».

**`download_url` de los recursos de 2024 ya registrados (tarea 6):** los 13 ZIP (`…/descarga/STATA/968-Modulo<1629…1641>.zip`) y los 7 PDF de M0-02 guardan su URL exacta de archivo; ninguno tiene solo la página general. Con los 3 documentos nuevos, los de 2024 registrados son 10 (códigos 1 a 9 y 11).

**YAML** `curados/inferencia/descargas/endes_2024.yaml` v0.2.0: `encuesta` con `periodo_codigo: 5` y `periodo_nombre: "Unico"`; `tablas` en los 13 módulos (34 `.dta`, sin el sufijo `_2024`); `codigo_documento` en 10 documentos (1 a 9 y 11); clave nueva `documentos_adicionales` con la ficha de 2025 (encuesta 1038) y el informe.

**Pruebas** (`uv run pytest -q tests/test_descargas_endes_2024.py`):
- RED sobre el YAML viejo: 7 fallos (URL/documentos, periodo, `codigo_documento`, `documentos_adicionales`, `tablas` 34 y `tablas` contra los ZIP).
- GREEN con el YAML nuevo: 9 pasan, incluida `test_tablas_iguales_a_los_dta_de_cada_zip_registrado` (marca `solo_mac`; lee los 13 ZIP del almacén con `abrir_zip_seguro` y falla si faltan, no salta).
