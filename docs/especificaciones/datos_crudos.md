# Capa cruda: obtención reproducible y metadatos

Versión 1 · 6 de octubre de 2026 · Estado: **aprobado por el dueño (6/10/2026)**.
Base: investigación sobre estándares de procedencia (`00_proyecto/investigacion/investigacion_metadatos.md`), validada por el orquestador.

## 1. Respuesta corta

- **No un pipeline por fuente, sino una receta por fuente.** Cada fuente del catálogo tiene un archivo de receta (YAML) que dice de dónde y cómo se obtiene. Unos pocos descargadores genéricos (7 estrategias) ejecutan las recetas. El código específico de cada fuente queda solo para leer y estandarizar el archivo, no para bajarlo.
- **El determinismo tiene dos niveles.** La *obtención* no siempre se puede repetir (una página cambia, una solicitud de acceso llega una vez). Lo que sí se garantiza es que **cada archivo obtenido queda congelado, identificado por su huella SHA-256 y descrito**, y que **todo lo que se calcula a partir de él es reproducible**.
- **Cada archivo crudo lleva un registro de metadatos** con un contrato fijo (sección 3) basado en estándares existentes: Frictionless Data Package v2, con nombres de campo tomados de DCAT 3 y PROV-O. Así la ficha de cada respuesta puede citar la fuente exacta.

## 2. Principios

1. **Un archivo se identifica por su contenido** (SHA-256), no por su URL ni por su nombre. Si un portal vuelve a publicar un archivo con el mismo nombre y otro contenido, se detecta como versión nueva.
2. **Los crudos son intocables**: se guardan una vez, en solo lectura, y nunca se editan ni se sobrescriben.
3. **Toda obtención termina igual**, sea automática o manual: archivo → huella → validación de forma → registro de metadatos.
4. **Idempotencia**: volver a correr una receta sin cambios en la fuente no crea nada nuevo; solo anota «sin cambio» en el registro de verificaciones.
5. **Las respuestas citan versiones fijas**, nunca «la última». Una respuesta de octubre sigue siendo reproducible aunque la fuente se actualice en noviembre.
6. **Las descargas de .gob.pe corren en tu laptop**; el resto del proceso puede correr en cualquier máquina.

## 3. Contrato de metadatos por archivo crudo

Cada archivo es un recurso dentro del `datapackage.json` de su captura. O = obligatorio, C = obligatorio si aplica, R = recomendado.

| Grupo | Campo | O/C/R | Ejemplo | Para qué sirve en la ficha |
|---|---|---|---|---|
| **Identidad** | `name` | O | `proyeccion-distrital-2018-2026` | Nombre estable del recurso |
| | `original_filename` | O | `6894980-peru-poblacion-total-proyectada….xlsx` | Se cita tal como lo publica la entidad |
| | `path` | O | `almacen/sha256/3b/01/3b0149…` | Dónde está el original (ruta lógica, nunca con `.zst`; ver §3.1) |
| | `hash` | O | `sha256:3b0149…` | **Identificador del crudo**; cualquiera puede verificarlo |
| | `bytes`, `mediatype`, `encoding` | O / O / C | `89640151`, `xlsx`, `latin-1` | Integridad y lectura correcta (del ORIGINAL, aunque se guarde comprimido) |
| | `pap_storage` | C | `{compression: zstd, path: …/<huella>.zst, bytes: 238418982}` | Forma de guardado si se registró comprimido (§3.1) |
| **Origen** | `source_id` | O | `INEI-PROYECCIONES-POBLACION-DISTRITAL` | Enlace con el catálogo (mismo ID) |
| | `publisher` | O | `INEI` | «Entidad» en la cita |
| | `dataset_title` | O | `Perú: Población total proyectada al 30 de junio… 2018–2026` | Título en la cita |
| | `access_url` | O | página de gob.pe | Enlace «ver en la fuente» |
| | `download_url` | C | URL del archivo; `null` si fue manual o por solicitud | Repetir la descarga |
| **Versión y fechas** | `source_version` + `source_version_basis` | C + O | `Boletín 2025` + `declarada` / `inferida` / `ninguna` | «Edición» en la cita, sin inventarla |
| | `temporal` | O | `2018–2026` | Período que cubren los datos |
| | `data_cutoff` + `data_cutoff_basis` | C + O | `2026-09-30` + `declarada` / `max_fecha_en_datos` / `desconocida` | «Datos al…» |
| | `issued`, `modified` | R | `2025-12-15` | Publicación y última actualización según la fuente |
| | `retrieved_at` | O | `2026-10-06T08:15-05:00` | «Consultado el…» |
| | `http_etag`, `http_last_modified` | C | cabeceras del servidor | Saber si cambió sin bajar todo |
| **Obtención** | `method` | O | `http_directo`, `http_patron`, `manual_navegador`, `scraping_navegador`, `solicitud_acceso`, `microdatos_encuesta`, `redatam_export`, `archivo_propio`, `geoservicio` | La ficha dice «descarga automática», «descarga manual», «solicitud Ley 27806»… |
| | `recipe` | O | `INEI-PROYECCIONES-POBLACION-DISTRITAL@a1b2c3d` | Receta y versión exacta usadas |
| | `attributed_to`, `tool` | O / R | `pap 0.1` o `Eber (manual, Firefox)` | Quién y con qué |
| | `manual_evidence` | C | huellas de una captura o PDF de la página | Prueba de qué se vio, en lo manual y el scraping |
| | `request` | C | expediente, fechas, huella de la respuesta | Solicitudes de acceso |
| **Licencia** | `licenses` + `license_basis` | O + O | `no declarada` + `declarada_en_pagina` / `norma_general` / `no_declarada` | No atribuir una licencia que la entidad no declaró |
| | `terms_note` | R | «Información pública (TUO Ley 27806)» | Límite legal |
| **Cambios** | `previous` | O | huella de la versión anterior o `null` | Cadena de versiones |
| | `change` + `change_summary` | O + R | `contenido`, `esquema`, `url`, `sin_cambio`, `nuevo` + filas antes/después | «Qué cambió» |
| | `derived_from` + `derivation` | C | huella del ZIP padre + `{tipo: descompresion, miembro: …}` | Archivos extraídos de un ZIP o tablas sacadas de un PDF |
| **Cobertura y calidad** | `spatial` | O | `{ámbito: PE, nivel_minimo: distrito}` | Nivel territorial al que sirve |
| | `known_issues` | R | «Último mes preliminar» | Sección de límites de la ficha |
| | `validation` | O | `{estado: valido_con_avisos, informe: …}` | Advertir problemas de calidad |

### 3.1 Crudos guardados comprimidos (decisión del dueño del 8/10/2026)

Los CSV y TXT de más de 10 MB se guardan como `almacen/sha256/aa/bb/<huella>.zst` (zstd nivel 9, un solo cuadro con el tamaño original en la cabecera y suma de control). Reglas:

- `hash` es **siempre** el SHA-256 del archivo original sin comprimir; `bytes` es su tamaño. `pap verificar` lo recalcula descomprimiendo en flujo (sin escribir nada en disco); `--rapido` compara `bytes` con el tamaño original anotado en la cabecera zstd y el tamaño del propio `.zst` con `cruda/almacen_zst.json` (registro versionado con `bytes_zst` y `sha256_zst` de cada `.zst`; detecta un `.zst` truncado). Cada compresión deja además una línea `accion: comprimir` en `verificaciones.jsonl`.
- `path` sigue siendo la ruta lógica `almacen/sha256/aa/bb/<huella>` (sin `.zst`). La forma real la resuelve el almacén (`almacen.resolver`): si no está el original, se usa `<path>.zst`. Por eso comprimir un crudo ya registrado **no cambia** su `datapackage.json`.
- No se usa el campo estándar `compression` de Frictionless porque declararía comprimido el archivo de `path`, que es el original. Los recursos registrados ya comprimidos llevan la extensión propia `pap_storage: {compression: "zstd", path: "<path>.zst", bytes: <tamaño del .zst>}`; sin ese campo, el recurso se registró sin comprimir (pudo comprimirse después con `pap almacen comprimir`).
- No se comprimen Excel, ZIP, PDF ni Parquet (ya vienen comprimidos y sus lectores no aceptan `.zst`). El umbral se cambia con `PAP_COMPRIMIR_MIN_MB` (o `no` para no comprimir al registrar).
- Restaurar un original: `zstd -d <huella>.zst -o <huella>` y comprobar `shasum -a 256 <huella>` = huella.

**Fecha de corte**: ningún estándar la define; es la única extensión propia (`data_cutoff` con su `basis`). Cuando la fuente no la declara se usa la fecha máxima presente en los datos, y se dice así en la ficha para no confundirla con un corte oficial.

## 4. Recetas y estrategias

Una receta por fuente en `curados/recetas/<source_id>.yaml`, versionada en git. Su `id` es el mismo del catálogo, y la estrategia sale del campo `estrategia_descarga` del catálogo.

| Estrategia | Catálogo | Qué hace | Nivel de reproducibilidad |
|---|---|---|---|
| `http_file` | `descarga_directa_url` | Descarga con petición condicional, calcula la huella y registra | Automática |
| `http_pattern` | `url_patron` | Expande la URL por año o mes; los períodos cerrados se congelan | Automática |
| `http_archive` | microdatos INEI (ZIP) | Descarga, extrae los miembros declarados (cada uno con `derived_from`) e incluye diccionario y DDI. Aún no construida: hoy el ZIP se registra entero con `pap registrar` (`zip` en `espera.formato`) | Automática |
| `geoservice` | `geoservicio` | Consulta paginada con orden fijo; guarda el resultado y la consulta exacta | Automática |
| `manual` | `descarga_manual` | No descarga: muestra los pasos, espera el archivo en la bandeja, lo verifica (nombre, tipo, tamaño, columnas) y lo registra; guarda una captura de la página | Guiada y verificada |
| `dashboard` | `scraping_dinamico` | Script de navegador que guarda los datos de red, el HTML y una captura; si no se puede, plantilla de solicitud de acceso | Evidencia guardada |
| `owner_file` | archivos propios | Registro único con metadatos declarados a mano y fuentes primarias identificadas | Declarada |

Ejemplo de receta manual (la mayoría de la ola 0):

```yaml
id: INEI-PROYECCIONES-POBLACION-DISTRITAL
strategy: manual
publisher: INEI
access_url: https://www.gob.pe/...            # página de la publicación
manual:
  pasos:
    - Abrir access_url y descargar el XLSX de la sección Documentos.
    - Anotar la fecha de publicación que muestra la página.
    - Guardar el archivo en biblioteca/cruda/bandeja/INEI-PROYECCIONES-POBLACION-DISTRITAL/
    - 'Ejecutar: pap registrar INEI-PROYECCIONES-POBLACION-DISTRITAL --issued <fecha>'
espera:
  formato: [xlsx]
  bytes: [100000, 20000000]
  columnas: [ubigeo, departamento, provincia, distrito, "2018", "2026"]
temporal: {inicio: 2018, fin: 2026}
spatial: {ambito: PE, nivel_minimo: distrito}
data_cutoff: {basis: desconocida}
```

## 5. Organización en la carpeta

```
biblioteca/cruda/
  almacen/sha256/aa/bb/<huella>[.zst]   # originales, solo lectura (no van a git); .zst = comprimido, misma huella
  capturas/<source_id>/<fecha>/datapackage.json   # metadatos de cada captura
  bandeja/<source_id>/                  # donde dejas las descargas manuales
  solicitudes/<source_id>/<expediente>/ # solicitudes de acceso y sus respuestas
  verificaciones.jsonl                  # cada revisión, incluidas las «sin cambio»
curados/recetas/<source_id>.yaml # recetas (sí van a git)
```

El índice de todas las capturas se carga en DuckDB para consultas como «¿qué fuentes llevan más de 90 días sin revisar?».

## 6. De la cifra publicada al archivo crudo

| Nivel | Identificador | Ejemplo |
|---|---|---|
| Respuesta | `ans_<id>` | una pregunta respondida |
| Cifra | `ans_<id>#c3` | 41,2 % |
| Indicador | `ind:<nombre>@<versión>` | `ind:anemia-6-35m@1.2.0` |
| Ejecución de cálculo | `run_<id>` + commit del código | |
| Tabla estandarizada | `std:<nombre>@sha256:<huella>` | |
| Archivo crudo | `sha256:<huella>` | |
| Captura | `<source_id>/<fecha>` | |
| Receta | `<source_id>@<commit>` | |

**Ficha corta**, una línea por fuente: *INEI, ENDES 2025 (microdatos, edición may-2026). Datos de ene–dic 2025. Consultado el 06-oct-2026. [Ver ficha completa]*

**Ficha larga**: cita completa, tabla de fuentes (archivo original, edición, período, corte, publicación, descarga, método, licencia, enlaces, huella abreviada), definición del indicador, cadena de procedencia, límites y aviso si hay datos más recientes que los usados.

**Formato de cita** (adaptado de DataCite y APA 7 para datos):
> Entidad (Año). *Título del conjunto* [archivo original], edición. (Conjunto de datos). Datos al <corte>. <URL de la página>. Consultado el <fecha>. SHA-256: <12 caracteres>.

## 7. Retención

| Qué | Regla |
|---|---|
| Crudo usado por una respuesta publicada | Permanente |
| Primera y última captura de cada período | Permanente |
| Capturas intermedias de fuentes diarias | 60–90 días, borrado solo con comando explícito y ensayo previo |
| Descargas manuales, solicitudes y archivos propios | Permanentes (no se pueden repetir) |

## 8. Herramienta

Una CLI pequeña propia, `pap` (`pap revisar | descargar | registrar | verificar | citar | almacen comprimir`), sobre `frictionless` (describir y validar) y `httpx` (descargas con reintento); la descompresión (`pooch`) se agregará con `http_archive`. Se descartan `datapackage-pipelines` y `Data Retriever` (sin mantenimiento); `dlt` queda para cuando haya fuentes con API.
