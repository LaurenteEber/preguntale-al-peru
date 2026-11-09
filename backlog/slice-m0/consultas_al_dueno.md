# Slice M0 — Consultas al dueño

Rigen las mismas reglas que en los slices anteriores (`agents.md` §5):
- **Tipo C o D:** van a «Consultas que bloquean».
- **Tipo B:** van a «Supuestos aplicados».

## Consultas abiertas desde el inicio

### K-06 — Formato de la serie ENDES (antes de M0-02) · **respondida el 9/11/2026: (a) Stata donde exista y SPSS en 2015–2020**
- **Qué pasa:** el INEI publica la ENDES 2021–2025 en Stata y en SPSS, pero la de 2015–2020 solo en SPSS. El cubo y los ZIP de 2024 que ya están registrados (módulos 1629 y 1638) son Stata.
- **Opciones:**
  - **(a) Stata donde exista y SPSS en 2015–2020.** No duplica las descargas de 2024 y compara contra el cubo con el mismo formato. El conversor normaliza los perdidos de los dos formatos.
  - **(b) SPSS en todos los años.** Hay que volver a bajar 1629 y 1638, y M0-10 compararía datos que vienen de SPSS con un cubo que viene de Stata.
- **Recomendación:** (a).

### K-01 — Aprobar la lista de ZIP de la ENDES 2024 (M0-02) · **aprobada el 9/11/2026, con condiciones**
- **Respuesta del dueño (9/11/2026):** «ok con k-01», sobre esta propuesta: los 13 módulos de 2024 en Stata (1629 a 1641; 1629 y 1638 `ya_registrado`, sin volver a bajar), la ficha técnica, los cuestionarios (hogar, individual y salud) y los diccionarios en PDF, solo con URL `https://proyectos.inei.gob.pe`. El dueño revisa la lista después.
- **Qué se pide:** revisar `curados/inferencia/descargas/endes_2024.yaml` y escribir aquí «aprobada» con la fecha.
- **Descarga:** si el agente no llega a `.gob.pe` desde el Mac, el dueño deja los ZIP en `biblioteca/cruda/bandeja/INEI-ENDES/`.
- **Hecho (9/11/2026, agente):** el Mac llegó a `proyectos.inei.gob.pe`. Se bajaron con `curl` (solo https, fallando ante error HTTP) los 11 ZIP de Stata que faltaban (1630 a 1637, 1639 a 1641) y los 7 PDF (ficha técnica, cuestionarios de hogar, individual y salud, diccionarios de hogar, individual y salud). Se comprobó que cada ZIP abre sin error y que cada PDF empieza con `%PDF`; los 18 quedaron registrados con `pap registrar` (`endes-2024-*`, capturas `2026-11-09` a `2026-11-09-18`). 1629 y 1638 no se tocaron. Tamaños en `evidencia/m0-02_tamano_zip.md`. Falta, hasta que el dueño ponga el token en uso, la subida real (`scripts/respaldar_crudos.sh`) y la restauración (`scripts/restaurar_crudos.sh`); ambos scripts están escritos y probados sin red, no se han corrido contra GitHub.

### K-02 — R en el Mac (M0-09) · abierta (prototipo ubicado)
- **9/11/2026:** el dueño indicó la carpeta de trabajo anterior (`~/Documents/SideProjects/pregunta-al-peru`). El prototipo está en `00_proyecto/investigacion/r_verificador/analista/verificar.R` (más los scripts del auditor en `auditor/scripts/`). Lo copia el agente en M0-09; falta confirmar la versión de R.
- **Qué dice el repo:** `docs/especificaciones/stack.md` registra que R ya se instaló en el Mac y que hay un prototipo del verificador en la carpeta de trabajo anterior (`00_proyecto/investigacion/r_verificador/`).
- **Qué se pide:**
  1. confirmar la versión con `R --version`;
  2. copiar `verificar.R` del prototipo a `verificador_r/` del repo.
- **Lo demás lo hace el agente:** `renv` 1.3.1, `survey` y `nanoparquet` 0.5.2.

### K-03 — Visto por lote: tablas curadas (M0-06) y recetas (M0-10) · abierta
- **Qué se pide:** leer los informes del auditor-agente (`evidencia/m0-06_revision.md` y `evidencia/m0-10_revision.md`) y escribir aquí «visto» con la fecha.

### K-07 — Umbrales de la regla de no respuesta del ítem (R-ENC-19) · abierta (tipo C; no bloquea M0)
- **Propuesta:**
  - si más del 5 % de las respuestas del grupo son «no sabe» o faltan, se avisa en «Más contexto»;
  - si pasan del 20 %, la cifra se marca «aproximada».
- **Qué se pide:** aprobar estos umbrales o dar otros. Mientras no se apruebe, la regla no se agrega y la tasa solo se informa en la capa 3.

### K-08 — Licencia de la ENAHO · abierta (no bloquea M0; se necesita antes de M3)
- **Qué pasa:** el repo principal es público. Los Parquet de la ENDES pueden publicarse (ODbL), pero la licencia de la ENAHO no está verificada.
- **Qué se pide:** confirmar si los Parquet de la ENAHO pueden ir al repo público. Si no, irán al repo privado de crudos.

### K-09 — Token de `gh` para el repo privado de crudos (M0-02) · **resuelta (9/11/2026)**
- **Qué pasa:** el repo `LaurenteEber/preguntale-al-peru-crudos` ya existe (9/11/2026).
- **Qué se pide:** crear un token de grano fino solo para ese repo, con `contents: write`, y guardarlo en el Llavero de macOS. El script lo pasa solo como `GH_TOKEN` del comando. Si el agente no puede usarlo, el dueño corre `scripts/respaldar_crudos.sh`.
- **De paso:** activar Push protection (secret scanning) en el repo público, en Settings → Code security.
- **Respuesta del dueño (9/11/2026):** hecho.
  - Token de grano fino `pap-crudos-respaldo`: solo `LaurenteEber/preguntale-al-peru-crudos`, con *Contents: read and write* (más *Metadata: read-only*), y vencimiento de 90 días.
  - Guardado en el Llavero de macOS con el servicio `pap-gh-crudos`. Se lee con `security find-generic-password -s pap-gh-crudos -w` y se pasa solo como `GH_TOKEN` del comando `gh`. Nunca se imprime ni se escribe en archivos.
  - Comprobación: `gh repo view LaurenteEber/preguntale-al-peru-crudos --json visibility` → `PRIVATE`.
  - Push protection activado en el repo público.
  - Si se filtra o vence: revocar o crear otro en GitHub (Developer settings → Fine-grained tokens) y reemplazarlo con `security add-generic-password -U -a "$USER" -s pap-gh-crudos -w`.

### K-04 — Horas por semana para revisiones y vistos · abierta (no bloquea M0)

### K-05 — Tope diario del LLM · abierta (se necesita en M1)
- **Propuesta:** US$ 5 por día (`docs/diseno/tecnologias.md` §8), más un tope por lote del enriquecimiento del índice de US$ 50.

## Consultas que bloquean (vacíos tipo C o D)

### D-M0-00b-1 — gitleaks marca 2 hallazgos en el historial · **resuelta el 9/11/2026**
- **Respuesta del dueño (9/11/2026):** «No es un secreto: es el enlace público de Power BI "Publicar en la web" del tablero del MEF (r= es base64 de {"k":id_reporte,"t":id_inquilino,"c":n}). Exclúyelo por fingerprint en .gitleaksignore, con un comentario.»
- **Aplicado:** los dos hallazgos tienen el mismo valor (misma huella sha256) y son el mismo enlace `app.fabric.microsoft.com/view?r=…` en `catalogo/scripts/catalogo_v03_base.json:1927` y `catalogo/catalogo_fuentes.json:3567`. Ambos excluidos por fingerprint en `.gitleaksignore`, con su comentario. No se tocó la regla ni el historial. `gitleaks git` sobre los 80 commits: **no leaks found**.
- **De paso:** el token falso de `tests/test_respaldar_crudos.py` (M0-02) se arma ahora por partes, como en `test_sin_secretos.py`, para que el gancho previo al commit no lo frene.
- **Qué pasa:** gitleaks 8.30.1 sobre los 83 commits encontró 2 coincidencias de la regla `grafana-api-key`, las dos en el commit `f98fb753` (4/11/2026): `catalogo/catalogo_fuentes.json` línea 3567 y `catalogo/scripts/catalogo_v03_base.json` línea 1927. Es la misma cadena en los dos archivos.
- **Qué es, a primera vista:** el campo `url_datos` de una fuente del catálogo, una URL de un informe público de Power BI (`app.fabric.microsoft.com/view?r=…`). Su parámetro `r` empieza con el mismo prefijo que usan las claves de Grafana, por eso salta. No parece un secreto, pero eso lo confirma quien conoce la fuente.
- **Por qué importa:** si fuera una clave real, habría que revocarla. El secreto no se copia aquí.
- **Qué se propone:** el dueño confirma que esa URL es el enlace público de la fuente. Si lo es, se agrega la huella de los dos hallazgos a un `.gitleaksignore` (el agente lo hace) para que `just secretos` quede en verde. Mientras tanto, el gancho antes de cada commit no se ve afectado (solo mira lo nuevo).


### C-M0-01-1 — Cambiar las reglas cambia la «huella de reglas» que llevan las respuestas · tipo C · **resuelta el 9/11/2026**
- **Respuesta del dueño (9/11/2026):** «Sí, regrabá (recomendado)». Se regrabaron `slice-2/base_estructurada` y `slice-3/base_api` con sus scripts y se cambió a 3 la aserción de `max_alternativas`. Detalle en `evidencia/m0-01_decisiones.md`, «Regrabación autorizada».
- **Qué pasa:** al aplicar las dos decisiones del 8/11 (`max_alternativas: 3` en R-LENGUAJE-05 y la cláusula de Benjamini-Hochberg en R-ENC-11), `reglas.json` cambia y con él la huella corta de reglas que toda respuesta lleva en «Para citar y verificar» (`14b83c8814a7`, antes `0682897f4b70`). **Ninguna cifra, semáforo, nivel de confianza ni texto de Q1–Q4 cambia**: se comparó la salida de `consultas_minimas/` con las reglas de antes y de después y solo difieren esas huellas (evidencia en `evidencia/m0-01_decisiones.md`).
- **Efecto en las pruebas:** 10 pruebas comparan la respuesta con una base grabada que incluye esa huella y fallan solo por eso: `test_cli_preguntar.py::test_via_estructurada_igual_a_la_base_de_s2_00`, `web/test_guiado.py::test_diferencias_con_la_base_api_solo_las_permitidas[q1..q4]`, `web/test_paginas.py::test_la_api_no_cambia_por_las_paginas`, `web/test_servicio.py` (3). Además, `test_no_se_puede.py::test_textos_y_motivos_de_la_regla` afirma `max_alternativas == 2`, que la decisión cambia a 3.
- **Por qué importa:** «la suite sin cambios» no se cumple tal cual. Las bases viven en `backlog/slice-3/evidencia/base_api/` y afines, fuera de lo que esta historia puede editar, y regrabarlas es decidir qué diferencias se aceptan.
- **Qué se propone:** aceptar la huella nueva y regrabar esas bases (y subir a 3 el valor que afirma `test_no_se_puede.py`) en una historia aparte o con el visto del dueño. El código del motor no cambia.


## Supuestos aplicados (tipo B)

- **M0-00b — límites de `abrir_zip_seguro`** (`curados/inferencia/parametros.yaml`, `almacen.zip_*`): 1 024 MB por miembro, 2 048 MB en total, proporción de compresión máxima 100 (solo en miembros de 1 MB o más), bloques de 1 024 KB. Margen sobre el ZIP más grande registrado (89,6 MB; 732 MB descomprimidos; proporción 28,3). `supuesto: M0-00b`.
- **M0-00b — regla del lock** (`seguridad.lock_dias_min` y `seguridad.lock_excepciones` en el mismo YAML): 14 días mínimo, sin excepciones registradas. `supuesto: M0-00b`.
- **M0-00b — versiones elegidas con la regla de 2 semanas:** Python 3.12.16 (la última 3.12.x), `uv` 0.13.5 en la imagen (la 0.13.7 tenía menos de 2 semanas), `pip-audit` 2.10.1. `exclude-newer = "2 weeks"` bajó `opentelemetry-api` a 1.45.1 y `python-multipart` a 0.0.32. `supuesto: M0-00b`.
- **M0-00b — pruebas sin red:** `pytest-socket` deja pasar solo el bucle local (`127.0.0.1`, `::1`, `localhost`) y los sockets Unix, porque la web y las pruebas con navegador usan un servidor local. `supuesto: M0-00b`.
- **M0-00b — A9:** `test_sin_secretos.py` busca el prefijo de GitHub seguido de un cuerpo de 20 o más caracteres (no el prefijo solo), porque la historia M0-00b y la auditoría previa nombran los prefijos en prosa. `supuesto: M0-00b`.
- **M0-00b — `puentes.py:262`** abre el ZIP del SIEN con `zipfile.ZipFile` y lo lee en flujo (`z.open`), no con `z.read()`; la historia solo pide los tres `z.read()`, así que no se tocó. Pasarlo por `abrir_zip_seguro` queda a criterio del dueño (tipo A, bajo riesgo).
- **M0-02 — URL de los PDF:** el listado oficial «Consulta por Documentos» del portal del INEI (ENDES 2024, periodo 5) da 11 documentos; se tomaron los 7 pedidos en K-01 (ficha técnica, 3 cuestionarios, 3 diccionarios), con la forma `.../Descarga/DocumentosMetodologicos/2024-5/<Nombre>.pdf` que ya documenta la receta `INEI-ENDES.yaml`. La ficha técnica también está en `.../FichaTecnica/968-Ficha.pdf` (mismo tamaño, 706 542 bytes); se usó la primera. No se bajaron los manuales (entrevistadora, antropometrista, supervisora) ni la identificación de bases, que K-01 no pidió. `supuesto: M0-02`.
- **M0-02 — nombres de recurso:** `endes-2024-<módulo en español>` (vivienda, datos-basicos-mef, historia-nacimiento, embarazo-parto, inmunizacion-salud, nupcialidad-fecundidad, sida-condon, mortalidad-materna-violencia, disciplina-infantil, salud, programas-sociales) y `endes-2024-<documento>` para los PDF. El dueño puede cambiarlos antes de M0-04. `supuesto: M0-02`.
- **M0-02 — respaldo:** los archivos de más de 2 GB se parten en pedazos de 1 900 MB (`.parte-aa`…); el servicio del Llavero por defecto es `pap-gh-crudos` (K-09). `almacen.repo_crudos` y `almacen.espacio_libre_min_gb` (50) agregados a `curados/inferencia/parametros.yaml` (`decision: F-03`). `supuesto: M0-02`.
