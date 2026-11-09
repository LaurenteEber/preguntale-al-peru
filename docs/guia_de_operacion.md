# Pregúntale al Perú — Guía de operación

Cómo preparar el entorno, mantener la biblioteca de datos, las tablas curadas y las reglas, y operar la web (§6). Para preguntar al motor: [manual_de_uso.md](manual_de_uso.md). Arquitectura: [arquitectura.md](arquitectura.md). Estado del proyecto: [estado.md](estado.md).

## 1. Preparar el entorno (una vez)

**Requisitos:** macOS o Linux, git y [uv](https://docs.astral.sh/uv/). uv instala Python 3.12 por su cuenta.

```bash
cd ~/Documents/SideProjects/preguntale-al-peru
git checkout main
uv sync --locked --no-build   # crea .venv con las versiones exactas de uv.lock, solo desde wheels; falla si el lock no está al día
uv run pap --help       # lista de comandos
```

**Importante:**
- **Instalar siempre con `--locked --no-build`** (M0-00b): `--locked` se niega a cambiar `uv.lock` y `--no-build` no ejecuta código de instalación de paquetes fuente. `pyproject.toml` fija `exclude-newer = "2 weeks"`: ningún paquete con menos de dos semanas de publicado entra al lock. Para subir una dependencia: auditoría con `backlog/plantillas/auditoria_dependencia.md`, `uv lock`, `just auditar`.
- Los **crudos** (`biblioteca/cruda/almacen/`) y los **Parquet** no están en git. Si clonas en otra máquina, hay que copiar el almacén desde un respaldo o volver a descargar las fuentes y reconstruir.
- Todos los comandos se corren con `uv run …` desde la raíz del proyecto.

### 1.1 Trabajar en local o en la nube

| | Mac del dueño (local) | Claude Code en la nube |
|---|---|---|
| Datos | Tiene el almacén de crudos (`biblioteca/cruda/almacen/`) | No tiene los crudos |
| Biblioteca | `uv run pap construir …` (solo aquí) y `uv run pap calcular` | `scripts/bajar_biblioteca.sh` baja los Parquet del release de GitHub; **después hay que correr `uv run pap calcular`** |
| Pruebas | Suite completa: `uv run pytest -q` | `uv run pytest -q -m "not solo_mac"` (se dejan fuera las que piden los crudos) |
| Clave del intérprete | `PAP_ANTHROPIC_API_KEY` en el entorno, cargada por el dueño; nunca se imprime ni se escribe en archivos | Ídem |

El release `biblioteca-010ea965` trae el cubo actual; si se baja otro (p. ej. `biblioteca-ba1fbc55`), `pytest` se detiene antes de la primera prueba con un solo mensaje, «el cubo local no es el del manifiesto: corre `pap calcular`», si el cubo local no es el del manifiesto (`tests/conftest.py`, `tests/test_cubo_manifiesto.py`). Si falta el cubo, esa comprobación no aborta: fallan por sí solas las pruebas que lo necesitan.

## 2. Consultar lo que ya está calculado

### 2.1 Ver las respuestas del piloto
Las del primer piloto tienen su referencia en `tests/referencias/q1.json` … `q4.json` (las nuevas salen en `salidas/preguntar/`, ver el manual §3.1), por capas: lo visible, «Más contexto», «Para citar y verificar» y, al final, el detalle técnico (tabla de cifras, ficha larga y reglas aplicadas). El `.json` trae lo mismo, estructurado; las capas van en `capas.capa1/2/3`.

### 2.2 Consultar el cubo de indicadores con SQL

```bash
uv run python - <<'PY'
import duckdb
print(duckdb.sql("""
  SELECT indicador_id, anio, nivel, territorio_nombre, round(valor,1) AS valor,
         round(ic_inf,1) AS ic_inf, round(ic_sup,1) AS ic_sup, n_muestra
  FROM 'biblioteca/indicadores/fact_indicador.parquet'
  WHERE indicador_id = 'endes_anemia_6_35m' AND territorio_id = '09' AND linea = 'cifra'
  ORDER BY anio""").df())
PY
```

**Claves:**
- `territorio_id`:
  - departamento con 2 dígitos (`'09'`);
  - distrito con 6 (`'150132'`);
  - ámbitos de Lima con nombre: `LIMA_METROPOLITANA`, `LIMA_REGION`, `CALLAO`;
  - nacional: `PE`.
- `nivel`: `nacional`, `departamento`, `provincia`, `distrito`, `establecimiento` o el ámbito.
- `linea`: `cifra` para la cifra principal; el gasto tiene además líneas aparte, como la de referencia nacional.

> La cifra del cubo **todavía no es una respuesta publicable**. Las reglas (precisión, nivel, quiebres, rótulos) se aplican en el motor (manual §3.1).

### 2.3 Citar una fuente
```bash
uv run pap citar INEI-ENDES            # cita completa de la última captura
uv run pap citar INEI-ENDES --corta    # una línea, para la ficha
uv run pap citar 3b014946              # por prefijo de huella
```

## 3. Mantener la biblioteca de datos

### 3.1 Ver el estado de las fuentes
```bash
uv run pap revisar                     # todas: estrategia, compuerta, capturas, días sin revisar
uv run pap revisar INEI-ENDES          # una: pasos de descarga y pendientes
```

### 3.2 Incorporar o actualizar un archivo de una fuente
1. **Descargar:**
   - Si la receta es automática (`http_file` o `http_pattern`): `uv run pap descargar <ID>`.
   - Si es manual: `pap revisar <ID>` muestra los pasos. Los sitios `.gob.pe` solo se descargan desde tu laptop, con el navegador. Deja el archivo en `biblioteca/cruda/bandeja/<ID>/`.
2. **Registrar:**
   ```bash
   uv run pap registrar <ID> --issued AAAA-MM-DD --nota "qué es"
   uv run pap registrar <ID> ~/Downloads/archivo.zip --recurso nombre-del-recurso   # o un archivo concreto
   ```
   Registrar dos veces el mismo archivo no lo duplica; queda anotado como «sin cambio».
3. **Verificar:** `uv run pap verificar <ID>`. Recalcula las huellas; `--rapido` solo revisa tamaños.
4. **Hacer commit** de `biblioteca/cruda/capturas/<ID>/…` y `verificaciones.jsonl`.

### 3.3 Reconstruir las tablas

Orden de dependencias:

```bash
uv run pap construir territorio
uv run pap construir poblacion        # ~3,5 GB de RAM
uv run pap construir puentes
uv run pap construir gasto            # el bloque más pesado
uv run pap construir endes
uv run pap construir enaho
uv run pap construir mapa_pobreza
uv run pap construir indicadores      # tablas curadas del piloto (curados/capa0)
uv run pap calcular                   # cubo fact_indicador
```

**Cómo se comportan:**
- **Usan exactamente los crudos fijados** en `curados/insumos.lock.yaml`. Para tomar capturas nuevas: `--actualizar-insumos`.
- **Se niegan a construir si:**
  - el código tiene cambios sin commit, salvo `--permitir-sucio`, que deja el manifiesto marcado como «sucio»;
  - falla una prueba bloqueante, salvo `--forzar`, que no se debe usar en producción.
- **Cada construcción escribe** su manifiesto (huellas de insumos, código y salidas) y un archivo de pruebas. La versión anterior queda en `historial/`.
- **Con los mismos insumos y el mismo código, la huella debe repetirse.** La huella actual está en `biblioteca/indicadores/manifiesto_p1_indicadores.json` (`tablas.fact_indicador.hash`) y empieza con `010ea965…`.

### 3.4 Editar datos curados (indicadores, doradas, cruces, listas)
1. Edita el archivo en `curados/capa0/`: `dim_indicador.yaml`, `cifras_doradas.csv`, `cruces_permitidos.yaml`, `grupos_oficiales_inei.csv`, etc.
   - **Doradas:** solo con cita de un documento oficial: `tipo_cita = oficial_inei`, u `oficial_ins` para el SIEN. La prueba DOR-04 rechaza cualquier otra.
   - **Doradas de registros** (SIEN): `proposito = control_registro`, tolerancia 0 y número de evaluados en `casos_publicados`. Se generan desde el archivo oficial con `curados/generadores/sien/generar_doradas_sien.py` (ver su `README.md`), sin transcribir a mano.
2. Haz commit y luego corre `uv run pap construir indicadores` y `uv run pap calcular`.
3. Corre las pruebas del piloto ([calidad.md](calidad.md), §3).
4. Registra la decisión en `docs/decisiones.md` si cambia un criterio.

### 3.5 Cambiar una regla
1. Nunca edites `reglas/reglas.json` ni `reglas.md`: son generados.
2. Agrega el cambio en `reglas/consolidador/ajustes_dueno.py` (bloque final, con fecha y fundamento).
3. Regenera: `python3 reglas/consolidador/consolida_reglas.py`. Se detiene si una prueba de consistencia falla.
4. Si la regla está en el alcance del validador, ajusta su función en `src/pap/motor/validador/` y sus casos en `tests/casos_validador/casos*`.
5. Corre `uv run pap validar-reglas` (y `--carpeta casos_implementador`) y las pruebas.

### 3.5b Seguridad: `just auditar` y el gancho de secretos (M0-00b)

```bash
brew install osv-scanner gitleaks   # una vez (versiones auditadas: osv-scanner 2.7.0, gitleaks 8.30.1)
just auditar                        # pip-audit + osv-scanner sobre uv.lock; sale con error si hay una vulnerabilidad abierta (necesita red)
scripts/instalar_ganchos.sh         # una vez por clon: gitleaks revisa lo preparado antes de cada commit (core.hooksPath = scripts/ganchos)
just secretos                       # gitleaks sobre todo el historial (secretos tapados en la salida)
```

- Correr `just auditar` en cada cambio de dependencias y al cerrar cada slice.
- Si el gancho detiene un commit, el secreto aparece tapado: se saca del cambio (nunca se copia a la evidencia) y, si ya estuvo en el historial, se avisa al dueño para revocarlo.
- Las pruebas no salen a internet (`pytest-socket` en `pyproject.toml`; solo el bucle local) y `tests/conftest.py` fija `HF_HUB_OFFLINE=1` y `SVYLAB_OFFLINE=1`. Una prueba revisa que `uv.lock` tenga hash en cada archivo, solo PyPI y nada con menos de 14 días, y otra prohíbe en `src/` las APIs peligrosas (C2, C6).
- El paquete de la biblioteca se compara contra la huella versionada en `curados/releases.yaml`; un release nuevo se agrega ahí, con su huella, en el mismo commit que lo anuncia.

### 3.6 Mantenimiento
```bash
uv run pap almacen comprimir --dry-run   # qué se comprimiría (texto > 10 MB, zstd, verificado)
uv run pap indice                         # reconstruye biblioteca/cruda/indice.duckdb
uv run pap recetas validar                # recetas contra el catálogo y R-DEP-01
just catalogo                             # recalcula la compuerta del catálogo (requiere just)
```

**Respaldo:** copia `biblioteca/cruda/almacen/` (1,2 GB) a un disco o una nube. Es lo único que no se puede regenerar sin volver a descargar.

### 3.7 Mapa de comandos de mantenimiento

| Comando | Para qué | Cuándo | ¿Escribe? |
|---|---|---|---|
| `pap revisar [ID]` | Estado de las fuentes: estrategia, compuerta, capturas, días sin revisar; con ID, los pasos de descarga y pendientes | Antes de actualizar una fuente | No |
| `pap descargar ID` | Descarga si la receta es automática; si es manual, muestra los pasos | Al incorporar una fuente | Almacén |
| `pap registrar ID [archivos]` | Guarda en el almacén un archivo de la bandeja o los indicados (`--issued`, `--recurso`, `--nota`…) | Después de descargar a mano | Almacén |
| `pap verificar [ID] [--rapido]` | Recalcula huellas (o solo tamaños) | Después de registrar | `verificaciones.jsonl` |
| `pap citar CLAVE [--corta]` | Cita de una fuente (ID) o de un archivo (prefijo de huella) | Para citar | No |
| `pap construir {territorio,poblacion,puentes,gasto,endes,enaho,mapa_pobreza,indicadores}` | Reconstruye una tabla curada o estandarizada | Tras cambiar crudos o código (solo en el Mac) | `biblioteca` |
| `pap calcular` | Reconstruye el cubo `fact_indicador.parquet` | Después de `construir`, o de bajar el release | `biblioteca` |
| `pap almacen comprimir [--dry-run]` | Comprime con zstd los textos grandes; `--dry-run` solo lista | Mantenimiento | Almacén (sin `--dry-run`) |
| `pap servir [--puerto N] [--red-local]` | Levanta la web en local (por defecto solo `127.0.0.1:8000`) | Para ver la web o probar la imagen | No |
| `pap indice` | Reconstruye `indice.duckdb` | Tras registrar capturas | `biblioteca` |
| `pap recetas {generar,validar,sincronizar}` | Recetas de descarga desde el catálogo; `validar` las contrasta con el catálogo y R-DEP-01 | Al tocar el catálogo | `validar`: no |
| `pap validar-reglas [--carpeta casos_implementador]` | Corre los casos de prueba del validador de reglas | Al cambiar una regla | No |
| `pap foto-pim` | **Desactivada** (8/10/2026): `registrar` y `extraer` se niegan; `listar` y `vistas` funcionan | No usar | No |

### 3.8 Qué se puede cambiar hoy y qué no
- **Sí, sin escribir código:** cualquier intención, tema, territorio y año de los 9 indicadores del piloto: el planificador arma las cifras (`curados/motor/intenciones.yaml`) y las plantillas genéricas redactan. Los textos están en `curados/motor/textos/` y los valores por defecto en `curados/motor/parametros_motor.yaml`.
- **Con trabajo:** un indicador o tema nuevo (tablas curadas, doradas y una fila en `intenciones.yaml`) o una intención nueva (una plantilla genérica y su texto, siguiendo el contrato por capas, `docs/especificaciones/contrato_respuesta.md`).

## 4. Operar el intérprete de texto libre (slice 2)

Cómo preguntar (opciones, `--texto`, aclaraciones, códigos de salida, cómo leer una respuesta, la matriz de cobertura y los formatos de consulta): [manual_de_uso.md](manual_de_uso.md) §3. Aquí solo lo que se mantiene.

- **Clave:** variable de entorno `PAP_ANTHROPIC_API_KEY` (nunca en archivos). Comprobar que existe sin mostrarla:
  `uv run python -c "import os; print(bool(os.environ.get('PAP_ANTHROPIC_API_KEY')))"`.
- **Apagar el intérprete:** quitar la variable. `--texto` responde entonces con el mensaje fijo y las opciones siguen igual.
- **Modelo, esfuerzo, precios y topes:** `curados/motor/parametros_motor.yaml` → `interprete` (`modelo`, `esfuerzo`,
  `precios_usd_por_millon`, `tope_por_corrida`, `reintento_proveedor`). El tope mensual real está en la consola del proveedor.
- **Ver el uso y el costo:** `salidas/interprete/uso.jsonl` (una línea por llamada: huella de la pregunta, consulta sin
  lugares, resultado, modelo, tokens y costo; nunca el texto). Sumar el costo:
  `uv run python -c "import json; print(sum(json.loads(l)['costo_usd'] for l in open('salidas/interprete/uso.jsonl')))"`.
- **Grabar** (solo preguntas del conjunto, de las pruebas o de las revisiones; nunca de personas reales, P-03):
  `uv run python tests/interprete/evaluar.py --grabar --solo <id>` o `--grabar --faltantes`.
- **Evaluar en vivo:** `uv run python tests/interprete/evaluar.py --evaluar --reporte <archivo.md> [--tope-costo 2]`. Usa
  las grabaciones que existen y solo llama por las que faltan (modo «completar»); corta en el tope.
- **Si cambia el prompt o el modelo:** cambia `version_prompt` y hay que volver a grabar (`--evaluar` lo hace) y borrar las
  grabaciones huérfanas. Cada cambio del prompt va en `backlog/slice-2/evidencia/cambios_prompt.md`.
- **Antes de cada commit:** `git diff --cached | grep -nE '^\+.*(<prefijo de clave>|<cabecera de clave>)'` debe salir vacío;
  `tests/test_sin_secretos.py` lo comprueba en todo el repositorio.

## 5. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| «El código tiene cambios sin commit» | Haz commit antes de construir; los manifiestos citan el commit |
| La huella del cubo difiere de la del manifiesto (`010ea965…`) | Revisa `uv sync` y la versión del commit. Si persiste, avisa: es un problema de reproducibilidad entre sistemas |
| «No space left» o memoria en `construir gasto` o `poblacion` | Libera disco; DuckDB usa una carpeta temporal y la población usa ~3,5 GB de RAM |
| No se puede descargar de `.gob.pe` | Descarga con el navegador a la bandeja y luego `pap registrar` |
| git dice «File exists» por un `.lock` | Otro proceso de git quedó a medias: cierra los editores y borra el `.lock` de `.git/` |
| Desde una sesión remota de Claude, git deja `.lock` o un commit sale vacío | La sesión no tenía permiso para borrar en la carpeta. Hay que darle permiso de borrado antes de usar git y verificar el árbol del commit (`git ls-tree -r HEAD`) en un paso aparte |
| Una dorada falla al construir | La cifra del INEI no se reproduce: revisa la definición, el criterio y la página citada. No uses `--forzar` |

## 6. Operar la web (slice 3)

Cómo usarla: [manual_de_uso.md](manual_de_uso.md) §3.1b. Rutas y códigos: [especificaciones/api.md](especificaciones/api.md). Hoy corre en local o en la red de la casa; no hay despliegue público (P-05, slice 4).

### 6.1 `pap servir`

```bash
uv run pap servir                    # 127.0.0.1:8000, solo este equipo
uv run pap servir --puerto 8123
uv run pap servir --red-local        # 0.0.0.0: también desde otros equipos de la red
```

- Host y puerto por defecto: `curados/web/parametros.yaml` → `servicio`. Un puerto inválido no arranca.
- Necesita la biblioteca (el cubo) en `biblioteca/`; en la nube, `scripts/bajar_biblioteca.sh` y luego `uv run pap calcular` (§1.1).
- Al arrancar, un hilo precalienta el motor con Q1–Q4 y una consulta por intención (`curados/web/precalentar.yaml`). Mientras tanto, `/salud` y las preguntas responden 503 «preparando». Medido: de 4,2 a 4,7 s hasta `/salud` 200, y 24,9 s en el primer arranque en frío tras sincronizar dependencias (`backlog/slice-3/evidencia/s3-08_rendimiento.md`).
- `GET /salud`: `{"estado": "ok"}` (200), `preparando` (503) o `error_precalentamiento` (503, el precalentamiento falló: revisa el registro; el nombre de la excepción queda en el registro, sin la pregunta).
- El mensaje de arranque se imprime antes de que el puerto esté abierto: espera a `/salud` antes de preguntar.
- `--red-local` abre el servicio a toda la red: úsalo solo en una red de confianza.

### 6.2 Imagen Docker

La receta es el `Dockerfile` de la raíz (Python 3.12.16 slim y `uv` 0.13.5 fijados por huella, usuario sin privilegios, dependencias con `uv sync --locked --no-build --no-dev`). Evidencia: `backlog/slice-3/evidencia/s3-09_imagen.md`.

```bash
docker build -t pap-s3-09:local .
docker run --rm -p 8000:8000 -e PAP_ANTHROPIC_API_KEY pap-s3-09:local     # la clave pasa del entorno, sin escribirla
```

- **Con la biblioteca ya bajada**, móntala en solo lectura (`dimensiones`, `estandarizada` e `indicadores`, en `/app/biblioteca/…`) y no se baja nada.
- **Sin ella**, `scripts/arranque_imagen.sh` la baja del release de GitHub (`biblioteca-010ea965`, o el que indique `PAP_BIBLIOTECA_ETIQUETA`) y comprueba la huella del paquete contra `curados/releases.yaml` (versionada en el repo) antes de descomprimir. Después compara la huella del cubo con la del manifiesto y, si no coincide, corre `pap calcular --permitir-sucio` (la imagen no lleva `.git`).
- Termina con `pap servir --red-local --puerto $PAP_PUERTO`: dentro de la imagen escucha en todas las interfaces (S3-09-a), y es `-p` el que decide qué se publica. Revísalo en el despliegue del slice 4.
- `HEALTHCHECK` sobre `/salud`, con 180 s de gracia para el precalentamiento y la descarga.

### 6.3 Variables de entorno

| Variable | Para qué | Por defecto |
|---|---|---|
| `PAP_ANTHROPIC_API_KEY` | Clave del intérprete de texto libre. Nunca en archivos ni en la imagen. Sin ella, el texto libre responde «no disponible» y el formulario guiado sigue | sin definir |
| `PAP_PUERTO` | Puerto de la imagen (lo lee `scripts/arranque_imagen.sh` y el `HEALTHCHECK`) | `8000` |
| `PAP_BIBLIOTECA_ETIQUETA` | Release del que la imagen baja la biblioteca si no hay una montada | `biblioteca-010ea965` |
| `PAP_RAIZ` | Raíz del proyecto dentro de la imagen | `/app` |

Fuera de la imagen, el puerto se elige con `--puerto`.

### 6.4 Límites

En `curados/web/parametros.yaml` → `limites` (todos `supuesto: S3-07`; el dueño los cambia editando una línea):

| Límite | Valor de hoy | Qué pasa al pasarse |
|---|---|---|
| Preguntas por IP | 10 por minuto (ventana deslizante de 60 s) | 429, «Espera unos segundos y vuelve a intentar»; lo escrito se conserva |
| Llamadas al LLM por día | 300 (día de Lima, reintentos incluidos; la caché de 24 h no cuenta) | 503 `tope_diario` solo en texto libre; el formulario guiado y la API con `consulta` siguen. Con los costos medidos, de US$ 0,72 a 5,40 por día |
| Cuerpo de la petición | 8 KB | 413 |
| Texto de la pregunta | 2 000 caracteres | 422 |

- Los contadores están **en memoria**: se reinician al reiniciar el servicio y no se comparten entre procesos. Es un solo proceso (slice 4 los revisa).
- La IP es la que ve el servidor; detrás de un proxy sería la del proxy (W-09, slice 4).
- Las páginas no ponen cookies, no cargan nada de terceros y envían `Content-Security-Policy`, `Referrer-Policy: no-referrer` y `X-Content-Type-Options: nosniff`.
- Objetivos de rendimiento y lo medido: `backlog/slice-3/evidencia/s3-08_rendimiento.md` (estructurada p95 0,27 s; texto con grabaciones p95 0,81 s; texto en vivo p95 3,13 s).

### 6.5 Comprobar que no se registra la pregunta (P-03)

La web no escribe archivos con la pregunta; el acceso guarda solo método, ruta (sin la consulta de la URL), código y tiempo; un error guarda el tipo de la excepción, sin mensaje ni traza. La única copia es la caché de interpretaciones de 24 h (`salidas/interprete/cache/`, P-03).

1. **Prueba automática:**
   ```bash
   uv run pytest -q tests/web/test_privacidad.py
   ```
   Hace 50 preguntas con un marcador (por texto, caja y formulario guiado), fuerza una excepción y comprueba que el marcador no aparece en los registros, ni en stdout y stderr, ni en archivos nuevos; también lo comprueba con uvicorn real. Evidencia: `backlog/slice-3/evidencia/s3-07_privacidad.md`.
2. **A mano:** con el servicio andando, haz una pregunta con una palabra rara (por ejemplo `zorzalprueba`) y busca esa palabra en lo que imprimió `pap servir` (o en `docker logs`) y en `salidas/`: solo debe aparecer en la caché de 24 h. En `salidas/interprete/uso.jsonl` solo hay huellas, nunca el texto.

Los nombres de personas escritos en la pregunta no se detectan (P-03): mientras el servicio no se abra a terceros es un riesgo aceptado, y se revisa en el slice 4.

## Anexo: referencia de la CLI de ingesta

Implementa [especificaciones/datos_crudos.md](especificaciones/datos_crudos.md). Toda obtención termina igual: archivo → huella SHA-256 → validación de forma → almacén → `datapackage.json` → registro de verificaciones → índice DuckDB.

### Comandos

| Comando | Qué hace |
|---|---|
| `pap revisar [ID]` | Estado de las fuentes: estrategia, prueba de humo, capturas, días sin revisar; con ID muestra pasos y pendientes |
| `pap descargar ID` | `http_file`/`http_pattern`: descarga condicional (ETag) y registra; `manual`: muestra los pasos. Otras estrategias: sprints posteriores |
| `pap registrar ID [ARCHIVOS…]` | Registra los archivos indicados o los de `biblioteca/cruda/bandeja/ID/`. Opciones: `--issued`, `--edicion`, `--corte`, `--evidencia`, `--nota`, `--forzar` |
| `pap verificar [ID] [--rapido]` | Recetas contra su esquema, cada `datapackage.json` contra Frictionless y el contrato, cada crudo contra su huella (los `.zst` se descomprimen en flujo; `--rapido`: solo tamaños) |
| `pap almacen comprimir [--min-mb N] [--dry-run] [--solo HUELLA] [--max-segundos S]` | Comprime con zstd los CSV/TXT del almacén de más de N MB (10 por defecto): escribe `<huella>.zst.tmp`, verifica que al descomprimir dé la misma huella y tamaño, lo renombra y **solo entonces** borra el original. Idempotente y reanudable (si se corta, se vuelve a correr). Si una verificación falla (o el disco se llena), el original queda intacto y sale con código 1. Anota cada `.zst` en `biblioteca/cruda/almacen_zst.json` (tamaño y SHA-256 del `.zst`, para `--rapido`) y cada cambio en `verificaciones.jsonl` (`accion: comprimir`). `--dry-run` solo lista |
| `pap construir territorio\|poblacion\|puentes\|gasto\|endes\|enaho\|mapa_pobreza` | Construye tablas curadas desde los crudos fijados en `curados/insumos.lock.yaml`: la capa 0 en `biblioteca/dimensiones/` y los insumos del piloto (S4: `endes`, `enaho`, `mapa_pobreza`) en `biblioteca/estandarizada/`. Parquet ordenado + manifiesto con huellas y pruebas; se niega si el código tiene cambios sin commit (salvo `--permitir-sucio`) o si falla una prueba bloqueante |
| `pap citar HUELLA\|ID [--corta]` | Cita del archivo (formato DataCite/APA adaptado) o línea de ficha corta |
| `pap indice` | Reconstruye `biblioteca/cruda/indice.duckdb` (tablas `recursos`, `verificaciones`, vista `fuentes_estado`) |
| `pap recetas generar\|validar\|sincronizar` | Genera recetas desde el catálogo (no sobrescribe sin `--sobrescribir`) o las valida. `validar` también compara el bloque `catalogo:` de cada receta con `catalogo/catalogo_fuentes.json` y `bloquea_mvp` con R-DEP-01 de `reglas/reglas.json` (única fuente de los bloqueantes); `sincronizar` copia esos valores al bloque y valida |
| `pap foto-pim registrar ARCHIVO [--corte AAAA-MM-DD] [--mover]` | **DESACTIVADO (decisión del 8/10/2026): `registrar` y `extraer` se niegan.** Foto mensual del PIM (receta `MEF-FOTO-PIM-MENSUAL`): extrae la tabla `foto_pim` y registra el `{año}-Gasto-Mensual.csv` como captura fechada. `extraer [--rehacer]` la rehace desde el almacén; `listar` muestra las fotos y los meses que faltan; `vistas` imprime las vistas DuckDB. Guía: [guias/foto_pim_mensual.md](guias/foto_pim_mensual.md) |

### Flujo de una descarga manual

1. `uv run pap revisar INEI-PROYECCIONES-POBLACION-DISTRITAL` → muestra los pasos.
2. Descargar el archivo y dejarlo en `biblioteca/cruda/bandeja/INEI-PROYECCIONES-POBLACION-DISTRITAL/`.
3. `uv run pap registrar INEI-PROYECCIONES-POBLACION-DISTRITAL --issued 2025-12-31`.
4. Hacer commit de `capturas/` y `verificaciones.jsonl`. El archivo de la bandeja ya se puede borrar.

### Dónde queda cada cosa

| Qué | Dónde | ¿git? |
|---|---|---|
| Crudos (solo lectura, por huella) | `biblioteca/cruda/almacen/sha256/aa/bb/<huella>` o `<huella>.zst` (texto > 10 MB, misma huella del original) | no |
| Metadatos de cada captura | `biblioteca/cruda/capturas/<ID>/<fecha>/datapackage.json` | sí |
| Registro de verificaciones | `biblioteca/cruda/verificaciones.jsonl` | sí |
| Índice | `biblioteca/cruda/indice.duckdb` (derivado) | no |
| Recetas | `curados/recetas/<ID>.yaml` | sí |
| Esquema de recetas | `src/pap/esquemas/receta.schema.json` | sí |
| Foto mensual del PIM (derivada) | `biblioteca/estandarizada/gasto/foto_pim/foto_pim_<año>_<mes_ref>_<huella12>.parquet` + `.json` | no |

Las rutas `path` de los `datapackage.json` son relativas a `biblioteca/cruda/` y nunca llevan `.zst`: para abrir un crudo usa `almacen.resolver(rutas, rec["path"])` (o `insumos.ultimo(...).ruta`), que devuelve el `.zst` si el original está comprimido; DuckDB y pandas lo leen por la extensión. `pap registrar` guarda comprimidos los CSV/TXT de más de 10 MB (`PAP_COMPRIMIR_MIN_MB=N` o `no`). El campo `recipe` guarda `<ID>@<commit>` de la receta usada, por eso conviene hacer commit de una receta antes de usarla.
