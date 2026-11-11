# Revisión independiente por partes del slice M0 (10/11/2026)

**Cómo se hizo:** una revisión por cada historia con código, de M0-00b a M0-11. La hizo un revisor-agente independiente (`gentle-ai-verify`, solo lectura), que no escribió el código de esa historia. Miró tres cosas:

- **riesgo y seguridad:** entradas no confiables, aislamiento, token, borrados y datos crudos;
- **confiabilidad de las pruebas:** si prueban los criterios desde la interfaz pública, si hay saltos silenciosos y si las cifras se calculan solo donde corresponde (P-01);
- **criterios de aceptación:** uno por uno.

Cada revisor trabajó en una copia aparte del repo, corrió solo las pruebas de su historia y dejó `git status` limpio. La revisión nativa por lentes de Gentle está apagada en este clon (decisión del dueño L6, `odd/tasks/slice-m0.md`). M0-00 y M0-01 fueron sobre todo documentos y reglas: M0-01 se revisó junto con M0-02.

**Resultado:** 11 de 12 partes aprobadas con observaciones. **M0-11 salió bloqueante y quedó corregida.** Ninguna cifra cambió, y las 90 filas siguen iguales al cubo, también después de los arreglos.

| Parte | Commits | Pruebas del revisor | Veredicto | Altas/medias |
|---|---|---|---|---|
| M0-00b | 4787964, c1ceaff | 23 passed | aprobada con observaciones | 2 medias |
| M0-01 | d187ea8 | reglas regeneradas byte a byte; `vp3_checks` y `prueba_guardia` en verde | aprobada con observaciones | — |
| M0-02 | ff72c46 | 36 passed | aprobada con observaciones | 1 media (ya superada) |
| M0-03 | 708ea02, c9dbffc | cubo `010ea965` idéntico; 0,0 de diferencia en 48 319 filas | aprobada con observaciones | 1 media |
| M0-04 | b4e41f1 | 31 passed | aprobada con observaciones | 2 medias |
| M0-05 | 9b95504 | 46 passed (1 falla porque la copia no tiene `.git`) | aprobada con observaciones | 1 media |
| M0-06 | 1389685 | 34 passed; `validar-tablas` sale con 0 | aprobada con observaciones | 1 media (consulta ya abierta) |
| M0-07 | d220e43 | 217 passed | aprobada con observaciones | 1 media |
| M0-08 | 86e0b03 | 49 passed | aprobada con observaciones; falta Linux | 2 medias |
| M0-09 | e925215, 2847b2b, f61aed0 | 45 passed (1 falla porque la copia no tiene `.git`) | aprobada con observaciones | 1 media → consulta C-M0-11-2 |
| M0-10 | d89db55, 9cac1fe | 38 + 18 passed; CSV de las 90 filas regenerado idéntico | aprobada con observaciones | 1 media |
| M0-11 | 75df63b, 51769f7 | 16 passed + 6 pruebas propias (3 fallaron) | **bloqueante → corregida** | 1 alta, 2 medias |

`d89db55` es un commit del dueño rotulado «M0-09 renv.lock». En realidad trae la primera mitad del código de M0-10: se revisó con M0-10. No se reescribe la historia de git.

## Hallazgos y qué se hizo

La columna «Qué se hizo» usa estos estados:

- **corregido M0-11:** arreglado en este slice, con una prueba que falla antes del arreglo y pasa después;
- **consulta:** decisión del dueño;
- **M1:** queda en la lista para el slice siguiente (`cierre.md`);
- **anotado:** solo se registra.

### M0-11 (bloqueante, corregida)

| ID | Sev. | Qué | Qué se hizo |
|---|---|---|---|
| H11-1 | alta | `bloques.py`: `original_filename` con ruta. Un `datapackage.json` editado a mano daba por respaldado un ZIP que no estaba en el release, y después `liberar` borraba la única copia. | corregido M0-11: `nombre_simple` rechaza rutas, `.` y `..`. Prueba `test_restaurar_no_acepta_original_filename_con_ruta`. |
| H11-2 | media | Los nombres de `SHA256SUMS` se aceptaban con ruta absoluta. | corregido M0-11: misma validación. Prueba `test_restaurar_rechaza_nombres_con_ruta_en_sha256sums`. |
| H11-3 | baja | Una línea de `SHA256SUMS` mal formada daba una traza y no quedaba en la bitácora. | corregido M0-11: se valida con una expresión regular y todo error queda en la bitácora como `fallo`. Prueba `test_restaurar_sha256sums_mal_formado_falla_con_mensaje`. |
| H11-4 | baja | Reposición de un objeto liberado: quedaba un `.tmp` si fallaba, no había `fsync` y el objeto no quedaba en solo lectura. | corregido M0-11: `try/finally`, `fsync` y `_solo_lectura`. |
| H11-5 | baja | Un ZIP liberable con la misma huella que uno protegido (hogar o anemia) borraba el objeto protegido. | corregido M0-11: «lo usa otro recurso» ahora cuenta los protegidos del mismo bloque. Prueba `test_liberar_no_borra_un_objeto_que_comparte_huella_con_un_protegido`. |
| H11-6 | baja | `liberar` confía en `bloques` de `almacen_zst.json`, un archivo versionado, sin contrastarlo con la línea `restaurar ok` de `verificaciones.jsonl`. | M1 |
| H11-7 | media | Faltaban pruebas de nombres con ruta, de un `SHA256SUMS` mal formado y de un token que `gh` escriba en su salida de error. | corregido M0-11: las 5 pruebas de arriba, más `test_restaurar_no_imprime_token_si_gh_falla`. |

### Corregidos en M0-11 desde otras historias (sin cambio de cifras)

| ID | Sev. | Historia | Qué | Prueba |
|---|---|---|---|---|
| H07-1 | media | M0-07 | La conexión DuckDB endurecida dejaba hacer `COPY … TO` y `CREATE` dentro de las carpetas permitidas. Ningún plan ni LLM podía llegar ahí, pero la barrera dependía solo de la gramática. Ahora todo el SQL compilado pasa por `ejecutar_select`, que acepta una sola sentencia y de tipo `SELECT`. | `test_duckdb_seguro.py::test_ejecutar_select_rechaza_copy_a_una_carpeta_permitida_y_no_toca_el_archivo` y 3 más |
| H07-2 | baja | M0-07 | `--` o `/*` en una expresión curada comentaba el resto. Ahora se rechazan fuera de los textos entre comillas. | `test_plan_gramatica.py::test_calificar_expresion_rechaza_comentarios_sql` |
| H06-2 | baja | M0-06 | `Predicado.var` iba sin comillas y `_EXPR_SEGURA` aceptaba subconsultas. Ahora `var` debe ser `^[A-Z][A-Z0-9_]*$`, y `SELECT` y `FROM` se rechazan como palabras. | `test_tablas_curadas.py::test_predicado_var_solo_acepta_nombres_de_variable` y otras 2 |
| H09-2 | baja | M0-09 | `verificada=True` era el valor por defecto. Ahora es obligatorio y solo por nombre. | `test_compuertas.py::test_verificada_es_obligatoria_y_solo_por_nombre` |
| H09-4 | baja | M0-09 | Una cifra suprimida guardaba «menos de X %» en un motivo. Ahora no queda ningún rótulo. | `test_compuertas.py::test_suprimida_no_deja_ningun_rotulo_en_los_motivos` |
| H10-1 | media | M0-10 | `validar` no exigía todas las doradas del indicador y año, así que se podía omitir la que no reproduce y llegar igual a `verificado` (E-05). Ahora reporta cada dorada que falta. Las 3 recetas reales siguen con ✔ (21 doradas). | `test_recetas.py::test_validar_detecta_una_dorada_de_la_tabla_que_la_receta_no_lleva` |
| H00b-5 | baja | M0-00b | `just secretos` no revisaba todas las ramas. Ahora lleva `--log-opts=--all`. | (configuración) |
| H02-3 | baja | M0-02 | Una prueba que lee los crudos no llevaba la marca `solo_mac`. | (marca) |
| H02-2, H00b-4 | baja | M0-02, M0-00b | Las filas del README del slice estaban desactualizadas o rotas. | (documento) |

### Consultas al dueño

| ID | Historia | Qué | Consulta |
|---|---|---|---|
| H09-1 | M0-09 | Con 25 a 49 casos, una cifra con un CV muy alto queda «referencial» en vez de suprimirse. R-ENC-03 y R-ENC-04 exigen n ≥ 50; el diseño §15.1 dice que el paso 2 «sigue». Manda `reglas.json`, que es lo que ya hacía el cubo. Una prueba fija el comportamiento de hoy. | **C-M0-11-2** |
| H06-1 | M0-06 | La relación 2024–2025 es `independiente`, no `conglomerados_repetidos` como pide la historia. | C-M0-06-1 (ya abierta) |
| H03-2 | M0-03 | `wcwidth` entró con `ftfy`. | D-M0-03-1 (ya abierta) |
| H04-1 | M0-04 | macOS no hace cumplir `RLIMIT_AS`. El único tope de memoria es el vigía de memoria residente (cada 0,2 s), que puede llegar tarde ante una asignación enorme. | supuesto ya anotado. Propuesta para M1: revisar filas × variables con `metadataonly` antes de leer, o el visto del dueño para aceptar el vigía en macOS. |

### Para M1 o después

| ID | Sev. | Qué |
|---|---|---|
| H00b-1 | media | `test_lock_seguro.py:54-65`: la prueba «detecta un lock malo» no pasa el lock falso por las comprobaciones reales. Hay que sacarlas a funciones. |
| H00b-2 | media | `scripts/auditar.sh` corre `pip-audit` con `uvx`, sin huellas ni regla de 2 semanas. `pip-audit`, `osv-scanner` y `gitleaks` no tienen su auditoría con la plantilla. |
| H00b-3 | baja | Ninguna prueba comprueba que `pytest-socket` está activo. Agregar `test_red_bloqueada.py`. Las consultas DNS y los subprocesos no quedan cubiertos. |
| H00b-6 | baja | `zip_seguro.py`: un error de CRC sale como `BadZipFile` y no como `ZipInseguro`. Falta una proporción de compresión total del ZIP. |
| H00b-7 | baja | El ZIP del SIEN (`capa0/puentes.py:262`) todavía no pasa por `abrir_zip_seguro`. |
| A6 | — | La imagen Docker no se construyó (el demonio estaba apagado). Riesgo extra: `uv sync --no-build` podría no instalar el propio `pap`. Probarlo en el primer `docker build`. |
| H01-1 | baja | La base de la API se regeneró desde un árbol con 15 archivos sin commit (`MANIFIESTO.txt`). |
| H02-4, H02-5 | baja | `respaldar_crudos.sh` usa `original_filename` sin `basename`, y `--clobber` puede reemplazar un respaldo bueno. |
| H03-1 | media | No quedó guardada la salida de pytest ni de Q1–Q4 de M0-03. La suite del cierre la cubre (`cierre.md`). |
| H03-3 | baja | La licencia MIT de `svy-rs` se aprobó sin citar su archivo LICENSE. |
| H04-2 | media | `convertir` reemplaza los Parquet de a uno y escribe el manifiesto al final. Una falla a mitad de camino deja Parquet nuevos con el manifiesto viejo. Usar una carpeta de preparación y un cambio atómico. |
| H04-3 | baja | La regresión del conversor compara solo cantidad de filas, no el contenido. |
| H04-4 | baja | `huella_contenido_v1` puede colisionar con el separador `\x1f` o con NULL frente a `"\x00"`. Definir `huella_contenido_v2`. |
| H04-5 | baja | Todo SIGKILL se atribuye al límite de CPU. |
| H05-1 | media | `reparar_dos` vuelve a leer todo el texto como cp850 y corrompe otros caracteres (`¿Ni¤o?` → `┐Niño?`), y el control de mojibake no lo ve. 2024 no se afecta. **Corregirlo antes de indexar 2015–2020.** |
| H05-2 a H05-4 | baja | Nota de reconversión desactualizada; cambio de la conversión de M0-04 hecho dentro de M0-05; `coincidencia_universo_parquet` inserta `predicado_sql` crudo. |
| H06-3, H10-2 | baja | Si falta el índice, `validar-tablas` y `validar-recetas` se saltan en silencio la comprobación de variables y marcan ✔ igual. |
| H06-4 | baja | La unidad de `CSALUD01.QSSEXO` no coincide entre `cortes_estandar.yaml` y `archivos_endes_2024.yaml`. |
| H08-1 | media | La prueba de la llamada nativa larga depende de la velocidad de la máquina. En un Linux rápido podría fallar. |
| H08-2 | media | El criterio de Linux sigue abierto. Repetir allí el caso de 4 años con 192 dominios. |
| H08-3, H08-4 | baja | Carrera de SIGALRM entre el `return` y `alarm(0)`. El trabajador se reutiliza después de una alarma suave sin revisar su conexión. |
| H08-5 | baja | Quitar `\.0$` de los cortes convertiría «10.0» en «10». Hoy no ocurre. |
| H09-3 | baja | `compuertas.paso_no_respuesta_activo` nunca se lee. |
| H09-5 | baja | `renv/activate.R` puede bajar renv de internet si falta en la biblioteca local. La auditoría dice «no llama a la red». |
| H10-3 | baja | Una prueba de otro año lleva la marca `solo_mac` sin necesitar microdatos. |
| H10-4 | baja | `d89db55` está mal rotulado. Basta esta nota. |

## Verificación después de los arreglos

- **Pruebas de los archivos tocados:** 297 pasan. Con Parquet real (recetas, compuertas, verificador y ejecutor sobre microdatos), 69 pasan. Las 90 filas siguen iguales.
- **`pap inferencia validar-tablas` y `validar-recetas`:** las dos salen con 0.
- **Suite completa, `regresion_microdatos`, `auditar.sh` y gitleaks:** resultados en `cierre.md`.
