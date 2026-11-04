# Estado actual del proyecto

Corte: 4 de noviembre de 2026. Es una foto: se reescribe (no se le agregan capas) al cerrar cada fase o cuando cambia el estado de una fuente. Las decisiones vigentes y las pendientes del dueño están solo en `decisiones.md`; la historia, en `historia.md`.

## Resumen

| Capa | Estado |
|---|---|
| Catálogo de fuentes | v2: 418 fuentes; Ola 0 con 19 y Ola 1 con 29. 38 aprobadas (17 por captura verificada). `inferencia_verificada` de ENDES y ENAHO 2015–2025 hecha; ENLA sin verificar (`catalogo/inferencia_verificada.csv`) |
| Reglas | v1.1: 96 vigentes (93 MVP), 11 etapas; el validador del piloto aplica 68. `reglas.json` en «1.1-borrador» |
| Capa 0 (Ola 0) | Construida, auditada y corregida: territorio (`dim_ubigeo_historico` 1 893 distritos vigentes, con Sangani provisional; desde el 2/11 con la ortografía de T-02, pendiente de reconstruir), población (oficial, censada e IPF), gasto MEF 2023–2025 con trazabilidad de programas, RENIPRESS, IPC y SIEN 2025. Reproducible bit a bit |
| Insumos del piloto (S4) | ENDES 2015–2025 (236 869 niños), ENAHO 2024–2025 (67 393 hogares) y Mapa de Pobreza 2018; reproducen 136 cifras del INEI (±0,1 pp) |
| Tablas curadas del piloto | `dim_indicador` (9), `cruces_permitidos` (CR-01 activo) y `cifras_doradas` (206; todas con cita oficial; incluyen 30 del SIEN contra el INS) |
| Cubo, validador y motor | Cubo `fact_indicador` versión 1.2.0, huella `010ea965…` (adenda del slice 1, 4/11/2026: se agregaron 8 780 filas de gasto en soles constantes de 2025, `devengado_constante`; las 39 539 filas anteriores no cambiaron: `backlog/slice-1/evidencia/adenda/s1-12_comparacion_cubo.txt`). El release de GitHub `biblioteca-ba1fbc55` trae el cubo anterior; en la nube se recalcula con `pap calcular`. Validador de 68 reglas; motor por intenciones (slice 1, fase 5a): consulta mínima → resolver territorial → planificador → plantillas por intención → capas, con «no se puede» y aclaraciones; Q1–Q4 son su regresión y la matriz de cobertura lo prueba (`backlog/slice-1/evidencia/adenda/matriz.md`). 775 pruebas (en la nube corren 741: 34 llevan la marca `solo_mac` porque piden los crudos) |
| Repositorio | **Migrado el 4/11/2026** a `preguntale-al-peru`, autocontenido (la carpeta de trabajo anterior no se publica). Validado reconstruyendo todo desde los crudos: las 35 tablas salen iguales salvo 3 que cambian solo en textos de procedencia con rutas (`dim_indicador.tabla_origen`, `dim_tema_gasto.revisado_por`, `dim_glosario_gasto`); el cubo repite su huella `ba1fbc55…`; 748 pruebas en verde y matriz reducida sin fallos. Las etiquetas y commits citados abajo son de la carpeta de trabajo |
| Piloto (fase 4) | **Cerrado el 13/10/2026** (etiqueta `piloto-cerrado`) |
| Fase 5a (motor por intenciones, slice 1) | **Hecha el 3/11/2026** (etiqueta `slice-1-cerrado`, de la carpeta de trabajo); **adenda cerrada el 4/11/2026** (S1-11 a S1-16: gasto en soles constantes y observaciones de la revisión; etiqueta `slice-1-adenda-cerrada`). Cierre en `backlog/slice-1/evidencia/cierre.md` |
| Fase 5b y 5c (intérprete LLM, API y web) | **No iniciadas**; siguiente: slice 2 (`backlog/plan_slices.md`) |
| Almacén | 1,2 GB comprimidos (zstd). **Sin respaldo externo** |

## Qué falta, en orden

1. **Del dueño:** las decisiones pendientes X-01 a X-08 (`decisiones.md`, sección final) y el **respaldo externo del almacén**. Las que tocan el motor por intenciones siguen abiertas en su valor de hoy: X-02 (conteo en «¿cuántos?» del SIEN), X-03 (CR-01 con el gasto del mismo año) y X-04 (un solo intervalo visible); cambiarlas es editar una línea de `parametros_motor.yaml`.
2. **Adenda del slice 1** (`backlog/slice-1/adenda/`): gasto en soles constantes y observaciones medias de la revisión; AD-1 y AD-2 aprobadas el 4/11/2026. Empieza por reconstruir la biblioteca en el Mac (S1-11).
3. **Slice 2 (fase 5b):** intérprete LLM que produzca la consulta mínima (`backlog/plan_slices.md`); después 5c (API y web mínima) y beta cerrada.
4. **Consultas abiertas del slice 1:** ver `backlog/slice-1/consultas_al_dueno.md` y `backlog/slice-1/evidencia/cierre.md`.
5. **Antes de la Ola 1:** GA-13 (gasto en proyectos con códigos fuera del detalle de inversiones del MEF) y la separación por producto de las ejecutoras mixtas (X-06).
6. **Deuda menor:**
   - validar con terceros los 3 patrones de aviso del corrector (corpus de ≥ 40 oraciones escrito por otra persona);
   - prueba automática de campos fuera del diccionario (por escribir; la auditoría de reglas la hizo a mano);
   - URL de la Declaración de la Comisión Consultiva sobre la pobreza 2021;
   - registrar con `pap registrar --mover` los 16 PDF de las doradas, que esperan en `biblioteca/cruda/bandeja/validacion_doradas/` (fuera de git; sus huellas están en `tests/fixtures/validacion_doradas_SHA256SUMS`), sin dejar copia (F-04);
   - el Excel propio está dos veces (almacén y raíz de `biblioteca/cruda/`): son el mismo archivo (huella `3b014946…`); la copia de la raíz se puede quitar cuando haya respaldo;
   - revisar las doradas de 2025 cuando salga el informe definitivo de la ENDES 2025 (hoy preliminar);
   - Huancavelica 2015: bajar «ENDES 2015 Nacional y Departamental»;
   - `dim_dominio` 2025 sin ficha técnica confirmada;
   - la construcción de `fact_poblacion` usa ~3,5 GB de RAM (si crece, pasar el prorrateo a DuckDB);
   - el detalle de inversiones del MEF solo trae las activas: el 13–30 % del devengado en proyectos no se ubica por CUI;
   - limpieza: `.gitignore.tmp`, bloqueos `stale-*` y `tmp_obj_*` en `.git`.

## Ola 0 — referencia, denominadores y puentes (19 fuentes; del catálogo al 9/10/2026)

| Fuente | Compuerta | Base | Descarga | Bloquea el MVP (R-DEP-01) |
|---|---|---|---|---|
| `BCRP-IPC-LIMA` | aprobada | captura_verificada | api_rest | sí |
| `GITHUB-UBIGEO-PERU-AUMENTADO` | aprobada | captura_verificada | descarga_directa_url | sí |
| `INEI-CPV2017` | aprobada | captura_verificada | scraping_dinamico | sí |
| `INEI-DIRECTORIO-MUNICIPALIDADES` | aprobada | captura_verificada | descarga_manual | sí |
| `INEI-PNDA-UBIGEOS` | aprobada | captura_verificada | descarga_directa_url | sí |
| `INEI-PROYECCIONES-DEPARTAMENTAL-EDAD` | aprobada | captura_verificada | descarga_directa_url | sí |
| `INEI-PROYECCIONES-DISTRITAL-2018-2022` | aprobada | captura_verificada | descarga_manual | sí |
| `INEI-PROYECCIONES-POBLACION-DISTRITAL` | aprobada | captura_verificada | descarga_manual | sí |
| `MEF-DETALLE-INVERSIONES` | aprobada | captura_verificada | descarga_directa_url | sí |
| `MEF-MAESTRO-EJECUTORAS-DERIVADO` | aprobada | humo | descarga_manual | no |
| `PROPIO-ESTADISTICAS-SOCIALES-2020` | aprobada | captura_verificada | descarga_manual | sí |
| `RENIEC-POBLACION-IDENTIFICADA` | aprobada | captura_verificada | descarga_directa_url | no |
| `SUSALUD-RENIPRESS` | aprobada | captura_verificada | descarga_directa_url | no |
| `INEI-CPV2025` | enlace_confirmado | — | scraping_dinamico | no |
| `INEI-DIRECTORIO-CCPP` | enlace_confirmado | — | descarga_manual | no |
| `INEI-IDE-LIMITES` | enlace_confirmado | — | geoservicio | no |
| `MEF-PPR-PROGRAMAS-PRESUPUESTALES` | enlace_confirmado | — | descarga_manual | no |
| `MINEDU-ESCALE-PADRON` | enlace_confirmado | — | descarga_directa_url | no |
| `MINSA-POBLACION-ESTIMADA` | enlace_confirmado | — | scraping_dinamico | no |

## Ola 1 — núcleo (29 fuentes)

| Fuente | Compuerta | Base | Descarga |
|---|---|---|---|
| `CDC-VIGILANCIA-DATOS-ABIERTOS` | aprobada | humo | descarga_directa_url |
| `CUNAMAS-USUARIOS` | aprobada | humo | descarga_directa_url |
| `ESSALUD-DATOS-ABIERTOS` | aprobada | humo | descarga_directa_url |
| `FONCODES-PROYECTOS` | aprobada | humo | descarga_directa_url |
| `INEI-ENAHO` | aprobada | captura_verificada | descarga_directa_url |
| `INEI-ENAPRES` | aprobada | humo | descarga_directa_url |
| `INEI-ENDES` | aprobada | captura_verificada | descarga_directa_url |
| `INEI-MAPA-DCI-PROVINCIAL-2019` | aprobada | humo | descarga_directa_url |
| `INEI-MAPA-POBREZA` | aprobada | captura_verificada | descarga_manual |
| `INS-CENAN-SIEN` | aprobada | captura_verificada | descarga_directa_url |
| `JUNTOS-HOGARES-UBIGEO` | aprobada | humo | descarga_directa_url |
| `MEF-DA-GASTO-GPNNA` | aprobada | humo | descarga_directa_url |
| `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` | aprobada | captura_verificada | descarga_directa_url |
| `MEF-DA-TRANSFERENCIAS` | aprobada | humo | descarga_directa_url |
| `MEF-SEGUIMIENTO-PI` | aprobada | humo | descarga_directa_url |
| `MINEDU-CENSO-EDUCATIVO` | aprobada | humo | scraping_dinamico |
| `MINEDU-SIAGIE-DATOS-ABIERTOS` | aprobada | humo | descarga_directa_url |
| `MINSA-CNV-NACIDOS-VIVOS` | aprobada | humo | descarga_directa_url |
| `PAIS-TAMBOS-ATENCIONES` | aprobada | humo | descarga_directa_url |
| `PENSION65-USUARIOS` | aprobada | humo | descarga_directa_url |
| `PRONIED-INTERVENCIONES` | aprobada | humo | descarga_directa_url |
| `SIS-AFILIADOS` | aprobada | humo | descarga_directa_url |
| `SIS-ATENCIONES` | aprobada | humo | descarga_directa_url |
| `SUSALUD-DATOS-ABIERTOS` | aprobada | humo | descarga_directa_url |
| `WASIMIKUNA-IIEE` | aprobada | humo | descarga_directa_url |
| `MINEDU-UMC-ENLA` | enlace_confirmado | — | descarga_manual |
| `MINSA-INMUNIZACIONES` | enlace_confirmado | — | scraping_dinamico |
| `MINSA-REUNIS` | enlace_confirmado | — | scraping_dinamico |
| `MINSA-SINADEF` | enlace_confirmado | — | descarga_directa_url |

## Bloqueos conocidos

- **Red:** desde los entornos de trabajo de Claude no se puede descargar de dominios `.gob.pe`. Funciona: Claude en Chrome descarga a tu carpeta Descargas y `pap registrar` toma el archivo de ahí (usado en S1). WebFetch sí lee leyes.congreso.gob.pe y El Peruano.
- **Tableros sin descarga:** MINSA-REUNIS, MINSA-INMUNIZACIONES, MINSA-POBLACION-ESTIMADA e INEI-CPV2025 solo están en tableros; alternativas: extracción desde el navegador o solicitud de acceso a la información (Ley 27806).
- **Insumos bloqueantes del MVP (R-DEP-01):** 11, todos aprobados por captura verificada; se leen del catálogo (MEF-PPR salió el 8/10/2026).
- **Entorno local:** uv + Python 3.12 del proyecto (`uv sync` crea `.venv`; desde el 8/10 incluye `zstandard`). En la VM de Claude (desde el 2/11/2026) no se pudo instalar Python 3.12 por la red: las pruebas y las construcciones se corren en el Mac.
- **Descargas automáticas (`pap descargar`):** solo `http_file` y `http_pattern` en S0; `http_archive`, `geoservice` y `dashboard` se construyen cuando un sprint los necesite (mientras tanto: bandeja + `pap registrar`). Recetas con pendientes anotados: RENIEC (URL directa del archivo), RENIPRESS y ESCALE (cómo elegir el valor del patrón), MEF-MAESTRO-EJECUTORAS (fuente derivada, se construye en S3).

