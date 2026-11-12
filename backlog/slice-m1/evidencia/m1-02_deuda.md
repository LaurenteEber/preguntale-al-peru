# M1-02 — Deuda de M0

Se completa a medida que avanzan las tareas.

## Tarea 3 — H05-1: `reparar_dos` (12/11/2026)

- **Qué pasaba:** `reparar_dos` releía todo el texto como cp850 cuando encontraba ¤ ¥ ¢ £. Así arreglaba «Ni¤o», pero estropeaba otros signos: `¿Ni¤o?` salía `┐Niño?`. El control de mojibake no veía el `┐`.
- **Qué se hizo** (`src/pap/inferencia/indice.py`):
  - se cambia **cada carácter de DOS pegado a una letra** por la letra que representa (¤→ñ, ¥→Ñ, ¢→ó, £→ú, ‚→é; ¡→í solo detrás de una letra, porque delante de una palabra es el signo de exclamación); el resto del texto no se toca;
  - se mantiene la entrada de antes: solo se repara si el texto trae alguno de ¤ ¥ ¢ £, no trae vocales con tilde bien escritas y se puede escribir en cp1252;
  - el control de mojibake ve también los dibujos de caja (U+2500 a U+259F) que deja una relectura cp850.
- **Pruebas** (`tests/inferencia/test_indice_sintetico.py`): `test_reparar_dos_no_corrompe_signos_del_espanol_ni_otros_caracteres_H05_1` y `test_control_de_mojibake_ve_los_dibujos_de_caja_de_una_relectura_cp850_H05_1`. Fallaban antes del cambio y pasan después.
- **El índice de 2024 no cambia:** las 4 263 etiquetas distintas de `biblioteca/variables/*.parquet` dan la misma `etiqueta_curada`, los mismos arreglos y el mismo resultado del control con el código anterior y con el nuevo (0 diferencias).
- **Suite completa:** 1 820 pasan y 1 se salta (la base del slice: 1 818 y 1; las 2 nuevas son estas).

## Nota para la tarea 1 (pool)

El 12/11/2026, con el Mac ocupado por otro proceso (registro de documentos de M1-00), falló una vez `test_el_exceso_de_memoria_lo_corta_el_vigia_y_la_tarea_siguiente_funciona` en una corrida de `tests/inferencia/`; sola pasó 3 de 3. Es la misma familia que H08-1: el plazo cuenta el arranque del trabajador nuevo. Se revisa con la tarea 1.

Segunda vez (12/11/2026, suite completa mientras se calculaba el SHA-256 de 2,2 GB de modelos): la misma prueba falló con «DID NOT RAISE ErrorTemporal»: la tarea de 2 000 MB terminó sin que el vigía la cortara (tope de la prueba 1 100 MB). Sola pasa 5 de 5 y `tests/inferencia/test_pool_ejecutor.py` completo 10 de 10. Hipótesis: con presión de memoria, macOS comprime páginas y la memoria residente que mide el vigía no llega al tope. Se revisa en la tarea 1 (medir con la huella física del proceso o un tope del sistema, y una prueba que no dependa de la carga de la máquina).

---

# Resto de la historia (12/11/2026, agente implementador)

Ninguna tarea cambió una cifra. **Cubo:** `fact_indicador.parquet` sigue en `010ea965381c…`. **34 Parquet de microdatos:** los 35 archivos de `biblioteca/microdatos/` (34 Parquet y el manifiesto) tienen el mismo SHA-256 antes y después, y la `huella_contenido_v1` recalculada de los 34 coincide con la del manifiesto (0 diferencias). **90 filas de las recetas:** `pap inferencia receta <id> --anio 2024 --comparar-cubo` en las tres recetas da 30 de 30 filas con diferencia máxima 0 contra el cubo, 0 filas con estado o reglas distintos y las doradas se reproducen (9/9, 3/3, 9/9). No se corrió `pap construir` ni `pap calcular`. Suite completa: no se corrió (lo pidió así el encargo); se corrieron 240 pruebas de los archivos tocados y de los que dependen de ellos: todas pasan.

## Tarea 1 — Pool: el plazo cuenta desde que el trabajador está listo (H08-1 y observación de memoria)

- **Qué pasaba:** al reemplazarse un trabajador por `max_tasks_per_child`, su arranque (importar `svy`, abrir DuckDB) se contaba contra el plazo de la tarea siguiente.
- **Qué se hizo** (`ejecutor.py`): el trabajador marca una ranura de un arreglo compartido cuando empieza la tarea; el padre espera esa marca (con tope `arranque_max_s`, que da una caída «el trabajador no empezó») y solo entonces empieza a contar `timeout + gracia`. Un arranque lento ya no puede producir «tiempo».
- **Prueba sin depender de la máquina:** `PoolEjecutor(..., retraso_arranque_s=2.5)` hace que cada trabajador nuevo tarde 2,5 s a propósito (más que `timeout + gracia = 2 s`). RED: sin el arreglo, `test_el_arranque_lento_…` falló con «sin resultado en 2.0 s: trabajador terminado». GREEN: pasa. Otra prueba confirma que con arranque lento los tiempos suave y duro siguen cortando a tiempo.
- **Observación de memoria (el vigía no veía el exceso bajo presión):** el vigía medía `ru_maxrss`. Ahora mide el mayor entre `ru_maxrss` y lo que el sistema le carga al proceso: en macOS, la huella física (`ri_phys_footprint`, por `proc_pid_rusage`), que cuenta páginas comprimidas; en Linux, `VmRSS + VmSwap`. Pruebas (sin cargar la máquina): la huella física crece al tocar 300 MB; `_memoria_bytes` toma la mayor de las medidas aunque `ru_maxrss` quede bajo (con medidas falsas); `_vigia` corta justo en la medida que pasa el tope (medida inyectada). **Límite honesto:** no se puede provocar a voluntad la presión de memoria de macOS, así que la corrección se prueba por sus partes, no reproduciendo el fallo original; esas pruebas se escribieron junto con el código (no hubo un RED previo para ellas).
- **20 corridas seguidas** de `tests/inferencia/test_pool_ejecutor.py`: Mac, 20 de 20 en verde (15 pruebas cada una; [m1-02_pool_mac.txt](m1-02_pool_mac.txt)); Linux, 20 de 20 en verde (14 pasan y 1 se salta —la de la huella de macOS—; [m1-02_pool_linux.txt](m1-02_pool_linux.txt)).

## Tarea 2 — Linux y Docker (H08-2, A6)

Docker corrió con colima (autorizado el 12/11/2026; se encendió y se apagó al terminar). Imagen del proyecto construida con el `Dockerfile` (Linux aarch64, Python 3.12.16).
- **`uv sync --locked --no-build --no-dev` instala `pap`:** sí. El constructor compiló `preguntale-al-peru @ file:///app` y quedó el comando `pap`; `import pap` apunta a `/app/src/pap`. El riesgo A6 queda descartado.
- **`/salud`:** con `biblioteca/` montada en solo lectura, el contenedor dijo «El cubo coincide con el manifiesto», respondió 503 mientras se preparaba y luego **200 `{"estado": "ok"}`**.
- **4 años con 192 dominios en Linux:** nueva prueba `tests/inferencia/test_m102_cuatro_anios.py` con los topes de `parametros.yaml`: 192 dominios, 0,98 s dentro del trabajador, pico 616 MB (tope 1 536 MB). En el Mac: 0,94 s y 521 MB (`ru_maxrss`). Las pruebas del pool: ver tarea 1.
- Las imágenes y contenedores que creé se borraron (la imagen del proyecto y las bases `python:3.12.16-slim` y `uv:0.13.5` que bajó la construcción); las que ya estaban (`pap-s3-09`, `golang`, etc.) no se tocaron.

## Tarea 4 — H04-2: `convertir` cambia Parquet y manifiesto juntos

`inferencia/almacen.py`: escribe todo en `.<año>.preparacion` junto a la carpeta de salida y la pone en su lugar con dos renombres (la anterior se aparta como `.<año>.anterior` y se borra al final; si el segundo renombre falla se devuelve). Lo que había en la carpeta y la conversión no escribió se conserva. Si un corte dejó la carpeta apartada y sin poner la nueva, la siguiente corrida la recupera. Pruebas (`test_m102_convertir_atomico.py`): una falla a mitad de camino deja la carpeta anterior idéntica byte a byte y sin restos (RED: antes quedaban Parquet nuevos con el manifiesto viejo); sin carpeta previa no deja nada; la conversión buena conserva otros archivos; recuperación tras un corte. La prueba de punta a punta existente (`test_conversor_sintetico`) sigue en verde. No se reconvirtió nada real.

## Tarea 5 — H06-3 y H10-2: sin índice, fallan

`tablas_curadas.validar` y `recetas.validar` aceptan `exigir_indice`; los comandos `pap inferencia validar-tablas` y `validar-recetas` lo piden y marcan error («falta el índice de variables…») en las tablas que citan variables y en cada receta. Quien llama sin la opción (las pruebas con copias del repo, que no llevan el índice) no cambia. RED: 4 pruebas fallaban; PRESERVE: la quinta prueba fija que sin la opción no hay error nuevo.

## Tarea 6 — H00b-1 y H00b-2

- **H00b-1:** las comprobaciones del lock son funciones (`paquetes_fuera_de_pypi`, `paquetes_sin_hash`, `paquetes_recientes`) y la prueba «detecta un lock malo» pasa un lock falso por esas mismas funciones (también la excepción registrada y el archivo sin fecha).
- **H00b-2:** `scripts/auditar.sh` ya no usa `uvx`: instala `pip-audit 2.10.1` en un entorno temporal con `--require-hashes` desde una lista de 29 paquetes con huellas (todos con ≥ 14 días), y se detiene si `osv-scanner` o `gitleaks` no son la versión auditada; `just secretos` usa `scripts/auditar.sh --secretos`. Corrida real: pip-audit y osv-scanner limpios (86 paquetes) y gitleaks sin hallazgos (111 commits). Pruebas en `tests/test_m102_auditar.py`. Auditoría con la plantilla: [auditoria_herramientas_seguridad.md](auditoria_herramientas_seguridad.md). **Para el dueño:** `osv-scanner 2.7.1` tiene 3 días de publicada (regla: 14); queda como excepción temporal hasta el 23/11/2026 (el script avisa). No se agregó nada al lock.

## Tarea 7 — H00b-7: el ZIP del SIEN pasa por `abrir_zip_seguro`

`capa0/puentes.py` abre el ZIP con `abrir_zip_seguro`, copia cada CSV por bloques a un archivo temporal y lo lee de ahí. RED: un ZIP con ruta `Hb/../../fuera.csv` no se rechazaba; ahora lanza `ZipInseguro` (prueba `test_m102_puentes_zip.py`, más una de un ZIP bueno). **La tabla no cambia:** se calculó `puentes.construir` (sin escribir nada) antes y después con el SIEN real y la huella de cada tabla es idéntica (nueve tablas, p. ej. `fact_sien_hb_ubigeo`: 138 055 filas, `cbc10081…` antes y después).

## Tarea 8 — H11-6 y liberación

`bloques.py`: `liberar` (y su simulación) contrasta `almacen_zst.json` con la bitácora: debe haber una línea `restaurar`/`ok` de la fuente, con el id del bloque y el mismo release; si no, se detiene sin borrar y dice qué hacer. Además, dos ZIP liberables con la misma huella se tratan como un solo objeto (antes, el segundo `unlink` fallaba a medias): se borra una vez, se registran los dos en la bitácora y el total cuenta objetos. Pruebas nuevas en `tests/test_almacen_bloques.py` (3; RED: las 3 fallaban, la del doble ZIP con «No such file or directory»); las 21 anteriores siguen en verde.

## Tarea 9 — `duckdb_seguro.py`

El comentario decía que `COPY … TO` falla; dentro de las carpetas permitidas **no falla** (la prueba lo muestra: escribe), y fuera sí. Corregido: la barrera es `ejecutar_select`, y queda la nota para M4: esas carpetas deben ser de solo lectura en el servidor. Pruebas: `test_m102_duckdb_copy.py`.

## Tarea 10 — Menores

| ID | Estado |
|---|---|
| H00b-3 | **Hecho**: `tests/test_m102_red_bloqueada.py` comprueba que `pytest-socket` bloquea hosts externos y permite el bucle local y Unix. **No cubre** DNS ni subprocesos (anotado en la prueba). |
| H04-5 | **Hecho** (`almacen.ejecutar_aislado`): un SIGKILL se atribuye a la CPU solo si el subproceso gastó al menos el tope; si no, el mensaje dice «el sistema lo mató con SIGKILL … puede ser falta de memoria». |
| H08-3 | **Hecho** (`ejecutor._correr`): la alarma solo corta mientras la tarea corre; una que llega al desarmar ya no se escapa. Prueba que simula la carrera. |
| H08-4 | **Hecho**: tras una alarma suave el trabajador descarta su conexión DuckDB y la siguiente tarea abre otra. |
| H00b-6 | **No se hizo**: `zip_seguro.py` está fuera de las carpetas de esta tarea. |
| H02-4, H02-5 | **No se hizo**: son de `scripts/respaldar_crudos.sh`, fuera de las carpetas de esta tarea. |
| H04-3 | **No se hizo**: la regresión del conversor vive en `test_regresion_microdatos.py`, fuera de las carpetas de esta tarea. |
| H04-4 | **Solo propuesta** (ver abajo). |
| H06-4 | **No se hizo**: es una tabla curada (`cortes_estandar.yaml` / `archivos_endes_2024.yaml`): cambiar una unidad es tipo C. |
| H08-5 | **No se hizo**: hoy no ocurre; quitar el `\.0$` cambiaría cómo llegan los cortes numéricos, y eso toca cifras. |
| H09-5, H10-3 | **No se hizo**: `verificador_r/renv/activate.R` y la marca `solo_mac` de una prueba de otro año están fuera de las carpetas de esta tarea. |

### Propuesta H04-4: `huella_contenido_v2` (no aplicada)

`huella_contenido_v1` une las celdas con `\x1f` y escribe el nulo como `\x00`: una celda con `\x1f` dentro, o el texto «\x00» frente a un nulo, puede dar la misma cadena. v2 codificaría cada celda con su largo (`len:valor`) y el nulo con una marca que no pueda ser un largo. Cambiaría la huella de **todos** los archivos (los 34 Parquet de ENDES 2024 y el manifiesto), así que obliga a regrabar manifiestos y la restauración probada de `endes-2024`; por eso no se aplica. Propuesta: tratarlo como consulta al dueño y hacerlo junto con la próxima reconversión (M2), no antes.
