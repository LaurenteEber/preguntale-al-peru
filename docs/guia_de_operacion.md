# Pregunta al Perú — Guía de operación

Versión al 13/10/2026. Cubre lo que hoy funciona: la biblioteca de datos, el cubo y el motor del piloto, todo desde la Terminal. La web y las preguntas en lenguaje libre son de la fase 5. Arquitectura: `arquitectura_y_funcionamiento.md`.

## 1. Preparar el entorno (una vez)

**Requisitos:** macOS o Linux, git y [uv](https://docs.astral.sh/uv/). uv instala Python 3.12 por su cuenta.

```bash
cd ~/Documents/SideProjects/pregunta-al-peru
git checkout main
uv sync                 # crea .venv con las versiones exactas de uv.lock
uv run pap --help       # lista de comandos
```

**Importante:**
- Los **crudos** (`biblioteca/cruda/almacen/`) y los **Parquet** no están en git. Si clonas en otra máquina, hay que copiar el almacén desde un respaldo o volver a descargar las fuentes y reconstruir.
- Todos los comandos se corren con `uv run …` desde la raíz del proyecto.

## 2. Consultar lo que ya está calculado

### 2.1 Ver las respuestas del piloto
Las del primer piloto tienen su referencia en `tests/referencias/q1.json` … `q4.json` (las nuevas salen en `salidas/preguntar/`, ver 4.1), por capas: lo visible, «Más contexto», «Para citar y verificar» y, al final, el detalle técnico (tabla de cifras, ficha larga y reglas aplicadas). El `.json` trae lo mismo, estructurado; las capas van en `capas.capa1/2/3`.

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

> La cifra del cubo **todavía no es una respuesta publicable**. Las reglas (precisión, nivel, quiebres, rótulos) se aplican en el motor (§4).

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
- **Con los mismos insumos y el mismo código, la huella debe repetirse.** La del cubo actual es `ba1fbc55…` (3/11/2026).

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

### 3.6 Mantenimiento
```bash
uv run pap almacen comprimir --dry-run   # qué se comprimiría (texto > 10 MB, zstd, verificado)
uv run pap indice                         # reconstruye biblioteca/cruda/indice.duckdb
uv run pap recetas validar                # recetas contra el catálogo y R-DEP-01
just catalogo                             # recalcula la compuerta del catálogo (requiere just)
```

**Respaldo:** copia `biblioteca/cruda/almacen/` (1,2 GB) a un disco o una nube. Es lo único que no se puede regenerar sin volver a descargar.

## 4. Hacer una pregunta al motor

### 4.1 Preguntar con `pap preguntar`
Desde S1-06 hay tres formas de preguntar. Todas escriben `respuesta.json` y `.md` (por capas) en `--salida` (por defecto `salidas/preguntar`, fuera de git) e imprimen el texto validado y la ficha corta.

**a) Con opciones directas** (la consulta mínima, sin escribir un archivo):
```bash
uv run pap preguntar --intencion evolucion --tema anemia --territorio "departamento de Huancavelica"
uv run pap preguntar --intencion nivel_actual --tema desnutrición --territorio "Ayaviri, Melgar" --anio 2024
uv run pap preguntar --intencion comparacion --tema anemia --territorio "Puno" --comparar-con "Cusco"
uv run pap preguntar --intencion identificar_extremo --tema anemia --nivel departamento
```

| Opción | Qué hace |
|---|---|
| `--intencion` | `nivel_actual`, `evolucion`, `comparacion`, `cruce`, `identificar_extremo` o `efecto` |
| `--tema` o `--indicador` | El problema (`anemia`, `desnutricion_cronica`, `pobreza_monetaria`, `gasto_publico`; también alias como `desnutrición`, `pobreza`, `gasto`) o un id de `dim_indicador`. Un tema fuera del piloto se responde con la lista de temas que sí hay |
| `--territorio` | El lugar, como se escribe: «Puno», «Ayaviri, Melgar», «Lima Metropolitana», «Perú» |
| `--anio` o `--desde` / `--hasta` | Un año, o una serie. Sin periodo: el último año con datos (`evolucion`: toda la serie) |
| `--comparar-con` | El segundo lugar de una `comparacion` |
| `--nivel` y `--dentro-de` | Solo con `identificar_extremo`: el nivel de los lugares que se ordenan (hoy solo se responde para todo el país) |
| `--elegir N` o `--elegir N,N` | Responde una aclaración sin preguntar; con dos lugares ambiguos (una comparación), un número por lugar y en orden (ver abajo) |
| `--plan` | Imprime solo el plan de cifras (JSON), sin calcular ni escribir; sirve para depurar |
| `--salida` | Carpeta de salida |

**Aclaraciones.** Si el lugar es ambiguo (p. ej. «Huancavelica» es departamento, provincia y distrito) o falta el tema, el comando imprime las opciones numeradas, no escribe ninguna respuesta y sale con el código 2:
```text
Hay varios lugares llamados «Huancavelica». ¿Cuál quieres?
1) Huancavelica (departamento)
2) Huancavelica (provincia, departamento de Huancavelica)
3) Huancavelica (distrito, provincia de Huancavelica, departamento de Huancavelica)
```
Se responde repitiendo el comando con `--elegir 1`. Si no hay ninguna opción para elegir («No encontramos ese lugar…»), el comando no pide `--elegir`: escribe el lugar de nuevo.

**Comparaciones con dos lugares ambiguos.** `--elegir` toma un número por cada lugar que tenga opciones, en el orden en que se piden (primero `--territorio`, después `--comparar-con`):
```bash
uv run pap preguntar --intencion comparacion --tema pobreza --territorio "Cusco" --comparar-con "Puno" --elegir 1,1
```
Con un solo número, se aplica al primer lugar ambiguo y el comando vuelve a preguntar por el segundo (e imprime el ejemplo `--elegir 1,1`).

**Comparaciones entre dos lugares (R-ENC-11).** La respuesta dice cuál es mayor solo si la prueba estadística de diferencia lo permite (p < 0,05); si no, dice «sin diferencia estadísticamente clara». Si un lugar contiene al otro (p. ej. el país y un departamento) o una cifra no se puede publicar, muestra las cifras sin decir cuál es mayor.

**Códigos de salida** (`cli.codigo_salida` en `curados/motor/parametros_motor.yaml`): 0 respondida o «no se puede» (también se escribe, con su motivo), 2 aclaración pendiente, 1 error (consulta inválida, archivo que no existe, `--elegir` fuera de rango; el mensaje sale en lenguaje sencillo).

**b) Con una consulta mínima en un archivo, varios o una carpeta** (`curados/motor/consultas_minimas/` trae Q1–Q4):
```bash
uv run pap preguntar curados/motor/consultas_minimas/            # Q1–Q4
uv run pap preguntar curados/motor/consultas_minimas/q1.json --salida /tmp/respuestas
```
El archivo es el JSON de la consulta mínima (`curados/motor/esquemas/consulta_minima.schema.json`). El `respuesta.json` incluye la consulta mínima (`consulta_minima`), el plan generado (`plan`) y la versión de la biblioteca (`version_biblioteca`: cubo, commit y reglas). `tipo` dice si es `respuesta` o `no_se_puede`.

**c) Las consultas del piloto** (archivadas en `tests/fixtures/consultas_piloto/`; siguen funcionando):
```bash
uv run pap preguntar tests/fixtures/consultas_piloto/q1.yaml   # o varias: q1.yaml q2.yaml …
```
Escriben en `salidas/preguntar/qN.json` y `.md`, no en `00_proyecto/piloto/p3/respuestas/` (esa carpeta es solo el archivo del piloto y no se vuelve a escribir).

**Cómo leer una aclaración.** Una aclaración no es un error ni una respuesta: es el motor pidiéndote que precises. No lleva cifras ni capas, el comando sale con código 2 y no escribe ningún archivo de respuesta. Hay dos casos:
- *Lugar ambiguo*: la pregunta dice a qué se refiere («Hay varios lugares llamados «Huancavelica»…») y lista las opciones con su nivel y el lugar que las contiene. Elige el número que corresponde y repite **el mismo comando** agregando `--elegir N`. Para «Lima», las opciones son Lima Metropolitana, Lima Región y el Callao.
- *Falta el tema*: «¿De qué problema quieres saber?», con los temas que hay en orden alfabético. Repite el comando con `--tema`.
Si dice «Escribe el lugar de nuevo» no hay opciones: el lugar no se encontró; corrige el nombre. Un `--elegir` fuera de rango da un error con el rango válido.

**Correr la matriz de cobertura a mano** (≈ 5 000 consultas, ~5 min; la salida queda fuera de git):
```bash
uv run python tests/matriz/correr.py --salida salidas/matriz --reporte backlog/slice-1/evidencia/matriz.md
uv run python tests/matriz/correr.py --reducida --salida salidas/matriz   # solo los casos de pytest
```
`--limite N` corre solo los primeros N casos. El reporte cuenta los casos por clase (respondida, no se puede, aclaración, error), tema e intención y lista los fallos. Se espera 0 errores y 0 fallos. Requiere el cubo (`pap calcular`).

**Cuando no se puede.** Una pregunta que los datos no pueden responder da una respuesta de «no se puede» por las mismas capas: la respuesta corta dice primero lo que no se puede, «Lo más cercano que sí tenemos» ofrece una alternativa que el validador deja publicar (otro año, el nivel superior, el distrito de origen…) y el motivo va en «Más contexto». Nunca lleva una cifra. Si solo falta una parte, la respuesta se da y dice lo que falta. Los textos están en `curados/motor/textos/no_se_puede.yaml`.

### 4.2 Formato de una consulta del piloto (YAML)
```yaml
id: Q1
pregunta: ¿Cómo ha evolucionado la anemia en niñas y niños pequeños en Huancavelica?
intencion: evolucion            # nivel_actual | evolucion | comparacion | cruce | identificar_extremo | efecto
territorio: {nivel: departamento, id: "09", nombre_pedido: Huancavelica (departamento)}
periodo: {tipo: serie, desde: 2015, hasta: ultimo}   # o {tipo: ultimo}
plantilla: q1_evolucion
cifras:
  - {id: anemia_hvca_2025, indicador: endes_anemia_6_35m_oms2024, anio: ultimo, nivel: departamento,
     territorio: "09", rol: principal, comparar_con: 2024}
grupos: []                      # opcional: mapa_grupo_robusto | ranking_departamental
```

- `rol` es `principal` (decide el semáforo) o `contexto` (no lo sube por encima de ámbar).
- `comparar_con` pide una prueba de cambio frente a ese año (R-ENC-11). El validador la bloquea si cruza un quiebre de criterio o si uno de los años es 2020.

### 4.3 Qué se puede cambiar hoy y qué no
- **Sí, sin escribir código:** cualquier intención, tema, territorio y año de los 9 indicadores del piloto: el planificador arma las cifras (`curados/motor/intenciones.yaml`) y las plantillas genéricas redactan. Los textos están en `curados/motor/textos/` y los valores por defecto en `curados/motor/parametros_motor.yaml`.
- **Con trabajo:** un indicador o tema nuevo (tablas curadas, doradas y una fila en `intenciones.yaml`) o una intención nueva (una plantilla genérica y su texto, siguiendo el contrato por capas, `docs/especificaciones/contrato_respuesta.md`).
- **No, todavía:** preguntas en lenguaje libre (slice 2, con LLM) y la web.

### 4.4 Cómo leer una respuesta
- **Capa visible:**
  - respuesta corta;
  - cifra clave, con su fuente y si la entidad oficial publica la misma cifra;
  - «Ojo al leer»: lo que **no** se debe concluir;
  - confianza;
  - «¿Qué puedo hacer?», solo en temas de salud, con texto oficial.
- **Confianza en los datos** (antes, semáforo):
  - **alta** (verde): dato sólido;
  - **media** (ámbar): dato con limitaciones;
  - **baja** (rojo): dato muy aproximado, solo como referencia.
  - Habla de los datos, no de la situación. El color solo queda en el detalle técnico.
- **Respuesta «no se puede»:** misma estructura, sin cifra; la respuesta corta dice primero lo que no se puede, «Lo más cercano que sí tenemos» ofrece una alternativa y el motivo está en «Más contexto». `tipo` es `no_se_puede` en el JSON.
- **Más contexto:** cifras secundarias con su etiqueta «no se compara», avisos de las reglas y límites (fuentes, territorio, qué no permite concluir).
- **Para citar y verificar:** una línea de cita por cifra y el glosario.
- **Ficha corta:** confianza, fuentes y años, territorio, y qué **no** permite concluir.
- **Ficha larga, por cifra:** origen, territorio, qué mide, precisión (**nuestro intervalo y el del INEI**, con la nota de por qué difieren), método y **contraste con la cifra oficial del mismo criterio**.
- **Resultados de las reglas** (`resultados_respuesta`): cada regla aplicada, con su acción y su motivo.

## 5. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| «El código tiene cambios sin commit» | Haz commit antes de construir; los manifiestos citan el commit |
| La huella del cubo difiere de `ba1fbc55…` | Revisa `uv sync` y la versión del commit. Si persiste, avisa: es un problema de reproducibilidad entre sistemas |
| «No space left» o memoria en `construir gasto` o `poblacion` | Libera disco; DuckDB usa una carpeta temporal y la población usa ~3,5 GB de RAM |
| No se puede descargar de `.gob.pe` | Descarga con el navegador a la bandeja y luego `pap registrar` |
| git dice «File exists» por un `.lock` | Otro proceso de git quedó a medias: cierra los editores y borra el `.lock` de `.git/` |
| Desde una sesión remota de Claude, git deja `.lock` o un commit sale vacío | La sesión no tenía permiso para borrar en la carpeta. Hay que darle permiso de borrado antes de usar git y verificar el árbol del commit (`git ls-tree -r HEAD`) en un paso aparte |
| Una dorada falla al construir | La cifra del INEI no se reproduce: revisa la definición, el criterio y la página citada. No uses `--forzar` |

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
