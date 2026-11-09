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

### K-01 — Aprobar la lista de ZIP de la ENDES 2024 (M0-02) · abierta
- **Qué se pide:** revisar `curados/inferencia/descargas/endes_2024.yaml` y escribir aquí «aprobada» con la fecha.
- **Descarga:** si el agente no llega a `.gob.pe` desde el Mac, el dueño deja los ZIP en `biblioteca/cruda/bandeja/INEI-ENDES/`.

### K-02 — R en el Mac (M0-09) · abierta
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

(vacío)

## Supuestos aplicados (tipo B)

(vacío)
