# Pregúntale al Perú — Manual de uso

**Estado: al 4/11/2026, slice 1 y su adenda cerrados** (etiqueta `slice-1-adenda-cerrada`; la etiqueta `slice-1-cerrado` es de la carpeta de trabajo anterior y no existe en este repositorio, `docs/historia.md`). Hoy se usa desde la Terminal; lo que viene está marcado ⏳.

## 1. Qué es y para quién es

Pregúntale al Perú responde preguntas sobre problemas del país con **cifras de fuentes públicas oficiales**, por territorio y con los **límites de cada cifra**. Un error en una cifra o una respuesta mal leída es peor que no responder: por eso, cuando los datos no alcanzan, la respuesta dice primero lo que no se puede.

| Quién | Qué puede hacer hoy | Dónde seguir |
|---|---|---|
| **Dueño o analista** que usa la Terminal | Preguntar (§3), mantener la biblioteca de datos (§5), comprobar la calidad (§6) | Este manual y `guia_de_operacion.md` |
| **Público general** ⏳ | Escribir su pregunta en el celular y recibir la respuesta por capas | Slices 2 y 3 (§6) |

**Si solo vas a leer una sección:** ve a §3.1 (preguntar) y §4 (recetas «Quiero saber…»).

## 2. Leyenda

| Marca | Significa |
|---|---|
| ✅ | Disponible hoy (slice 1 o anterior). Cada comando marcado ✅ se corrió el 3/11/2026 y su salida es la que se muestra |
| ⏳ | Pendiente. Viene en el slice indicado (`backlog/plan_slices.md`). No hay comando todavía salvo que se diga |

## 3. Lo que ya funciona

### 3.1 ✅ Preguntar: `pap preguntar`

Todos los comandos se corren desde la raíz del proyecto con `uv run` (preparación del entorno: `guia_de_operacion.md` §1).

```bash
uv run pap preguntar --intencion evolucion --tema anemia --territorio "departamento de Huancavelica"
```

La pregunta tiene cuatro piezas: **intención** (qué quieres saber) + **tema** (de qué problema) + **territorio** (dónde) + **periodo** (cuándo; opcional). Escribe `respuesta.json` y `.md` en `--salida` (por defecto `salidas/preguntar`, fuera de git) e imprime la respuesta y su ficha corta.

#### Intenciones

| Intención | Qué responde | Notas |
|---|---|---|
| `nivel_actual` | Cuánto hay (último año con datos, o `--anio`) | |
| `evolucion` | Cómo cambió (serie, o `--desde`/`--hasta`) | Dice «sin cambio estadísticamente claro» si la prueba no respalda un cambio |
| `comparacion` | Dos lugares lado a lado (`--comparar-con`) | Dice cuál es mayor solo si la prueba lo respalda (R-ENC-11) |
| `identificar_extremo` | El lugar más alto de un nivel (`--nivel`) | Hoy solo para todo el país: con `--dentro-de` responde «no se puede». Ranking solo para anemia y desnutrición (departamental) y pobreza; el gasto no tiene ranking (R-GASTO-13) |
| `cruce` | Dos cifras lado a lado (gasto × anemia, CR-01) | No dice que una explique la otra |
| `efecto` | «¿Sirvió el gasto contra la anemia?» | Respuesta parcial: no hay evaluación publicada, muestra lo que sí se sabe |

#### Temas y alias

| Tema (`--tema`) | Alias aceptados | Indicadores (ids para `--indicador`) |
|---|---|---|
| `anemia` | — | `endes_anemia_6_35m_oms2024`, `endes_anemia_6_35m`, `sien_anemia_tamizados_6_35m`, `sien_cobertura_tamizaje_6_35m` |
| `desnutricion_cronica` | `desnutricion`, `desnutrición`, `desnutricion cronica`, `desnutrición crónica` | `endes_dci_menores_5` |
| `pobreza_monetaria` | `pobreza` | `enaho_pobreza_monetaria`, `mapa_pobreza_2018` |
| `gasto_publico` | `gasto`, `presupuesto` | `gasto_ex_pan`, `gasto_ex_pan_opcion_c` |

Los alias viven en `curados/motor/parametros_motor.yaml` (`temas.alias_cli`). Un tema fuera de la lista se responde con «Todavía no tenemos datos de ese tema» y los temas que sí hay (exit 0). Sin tema ni indicador, el comando pregunta el tema (exit 2). Con `--indicador` pides una cifra concreta en lugar del tema.

#### Territorios

| Cómo escribirlo | Qué pasa |
|---|---|
| `"departamento de Puno"`, `"Perú"`, `"Ayaviri, Melgar"` | Se resuelve directo |
| `Puno`, `Cusco`, `Huancavelica` (mismo nombre en varios niveles) | Pregunta cuál: departamento, provincia o distrito. Se responde con `--elegir N` |
| `Lima` a secas (T-03) | Pregunta: Lima Metropolitana, Lima Región o Callao |
| `San Juan` (homónimos entre distritos) | Pregunta con el distrito, la provincia y el departamento de cada opción |
| Nombre mal escrito o inexistente | «No encontramos ese lugar…» y exit 2, sin opciones: escríbelo de nuevo |
| Comparación con dos lugares ambiguos | `--elegir 1,1` (un número por lugar, en el orden `--territorio`, `--comparar-con`) |

Los nombres salen con tildes y ñ (T-02).

#### Opciones

| Opción | Para qué |
|---|---|
| `--intencion` | Una de las seis de arriba |
| `--tema` / `--indicador` | El problema, o una cifra concreta (id de `dim_indicador`) |
| `--territorio` | El lugar, como se escribe |
| `--anio` | Un año; sin él, el último con datos |
| `--desde` / `--hasta` | Serie (con `evolucion`); sin ellos, toda la serie con datos |
| `--comparar-con` | Segundo lugar de una `comparacion` |
| `--nivel` (`departamento`, `provincia`, `distrito`) y `--dentro-de` | Solo con `identificar_extremo` |
| `--elegir N` o `N,N` | Responde una aclaración sin preguntar. Se aplica a la primera aclaración y se ignora si no hay ninguna |
| `--plan` | Imprime solo el plan de cifras (JSON), sin calcular ni escribir. Para depurar |
| `--salida CARPETA` | Dónde escribir `respuesta.json` y `.md` |
| `consultas…` | Archivos `.json` (consulta mínima), `.yaml` (consulta del piloto) o carpetas con ellos |

#### Periodos y años con datos

| Cifra | Años | Territorios |
|---|---|---|
| Anemia ENDES, forma de medir vigente (`endes_anemia_6_35m_oms2024`) | 2024–2025 | país, departamento, Lima en tres ámbitos |
| Anemia ENDES, forma anterior (`endes_anemia_6_35m`) | 2015–2025 | ídem; **no se compara con la vigente** |
| Desnutrición crónica ENDES (`endes_dci_menores_5`) | 2015–2025 | país, departamento, Lima en tres ámbitos |
| Anemia SIEN (`sien_anemia_tamizados_6_35m`) | 2025 | establecimiento, distrito, provincia, departamento: solo de niños que se midieron la hemoglobina |
| Cobertura de tamizaje SIEN (`sien_cobertura_tamizaje_6_35m`) | 2025 | departamento y ámbitos de Lima (dos cotas) |
| Pobreza monetaria ENAHO (`enaho_pobreza_monetaria`) | 2024–2025 | país, departamento, Lima en ámbitos |
| Mapa de Pobreza (`mapa_pobreza_2018`) | 2018 | provincia y distrito, con rango (sin cifra puntual) |
| Gasto en servicios ex-PAN (`gasto_ex_pan`, `gasto_ex_pan_opcion_c`) | 2023–2025 | país, departamento, Lima en ámbitos; provincia y distrito solo gasto municipal y obras ubicadas |

Fuente de verdad: `curados/capa0/dim_indicador.yaml`. Un año o nivel sin datos da «no se puede» y ofrece lo más cercano.

#### Formas de pasar la consulta

```bash
# a) opciones directas (la consulta mínima, sin escribir archivo)
uv run pap preguntar --intencion nivel_actual --tema anemia --territorio "Ayaviri, Melgar"
# b) consulta mínima en JSON: un archivo, varios o una carpeta (Q1–Q4)
uv run pap preguntar curados/motor/consultas_minimas/q1.json
uv run pap preguntar curados/motor/consultas_minimas/
# c) consultas del piloto (YAML archivado, siguen funcionando)
uv run pap preguntar tests/fixtures/consultas_piloto/q1.yaml
```

Formato del JSON: `curados/motor/esquemas/consulta_minima.schema.json`; ejemplo (`q2.json`):

```json
{"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Ayaviri, Melgar"},
 "periodo": {"tipo": "ultimo"}, "pregunta_original": "¿Cuántos niños tienen anemia en Ayaviri (Melgar, Puno)?", "idioma": "es"}
```

Con varias consultas se escriben todas y el código de salida es el más grave. El `respuesta.json` incluye la consulta mínima, el plan y la versión de la biblioteca (`version_biblioteca`: cubo, commit y reglas).

#### Códigos de salida

| Código | Significa | Ejemplo |
|---|---|---|
| 0 | Respondida, o «no se puede» (también se escribe, con su motivo) | `nivel_actual` de desnutrición en un distrito |
| 2 | Aclaración pendiente: no se escribe respuesta | «Hay varios lugares llamados «Cusco»…» |
| 1 | Error de consulta, de archivo o de `--elegir` | `✘ La opción 9 no existe. Elige un número entre 1 y 3.` |

Valores en `cli.codigo_salida` de `parametros_motor.yaml`. Un valor inválido de una opción con lista (p. ej. `--intencion foo`) lo rechaza el propio argparse: imprime el uso y sale también con **2**, aunque no sea una aclaración. Si solo necesitas distinguir una aclaración, mira que la salida empiece con «Hay varios…», «¿De qué problema…» o «No encontramos…».

### 3.2 ✅ Cómo leer una respuesta

Una respuesta trae tres capas, la confianza y, al final, el detalle técnico (contrato completo: `docs/especificaciones/contrato_respuesta.md`).

| Parte | Qué contiene |
|---|---|
| **Capa 1, visible** (≈ 100 palabras, máximo 125) | Respuesta corta, **una** cifra clave con su fuente, «Ojo al leer» (1 a 3 viñetas con lo que **no** debes concluir) y la confianza |
| **Capa 2, «Más contexto»** | Cifras secundarias (con «no se compara» cuando aplica), avisos de las reglas y límites |
| **Capa 3, «Para citar y verificar»** | Una cita por cifra, glosario y, solo en salud, «¿Qué puedo hacer?» con texto oficial (pendiente de revisión del dueño, X-01) |
| **Detalle técnico** | Tabla de cifras, ficha larga, reglas aplicadas. Solo para auditoría |
| **Confianza en los datos** | `alta` (dato sólido), `media` (con limitaciones) o `baja` (muy aproximado). Habla de los datos, no de la situación; sin colores en la capa visible (R-05) |

**Tres tipos de respuesta** (`tipo` en el JSON):

| Tipo | Cuándo | Se reconoce porque… |
|---|---|---|
| `respuesta` | Hay cifra publicable | Trae cifra y confianza |
| `no_se_puede` | Los datos o las reglas no lo permiten | Empieza con «No…» o «Todavía no…», **nunca** trae una cifra, ofrece «lo más cercano» y da el motivo en la capa 2 |
| `aclaracion` | El lugar es ambiguo o falta el tema | Solo pregunta y numera las opciones; exit 2 |

Ejemplo real (`pap preguntar --intencion comparacion --tema pobreza --territorio Cusco --comparar-con Puno --elegir 1,1`, recortado):

```text
===== comparacion__pobreza_monetaria__08__21 · semáforo: verde
En 2025, la pobreza monetaria fue mayor en Puno que en Cusco, con una diferencia estadísticamente clara.
18,8 % de personas en situación de pobreza monetaria en Cusco en 2025, frente a 37,5 % en Puno.
No leas esta cifra como exacta: es una estimación de una encuesta, con margen de error. [...]
--- ficha
Confianza en los datos: alta (dato sólido): hay suficientes datos y son de 2025.
Datos de: ENAHO 2025 (INEI)
Territorio: departamento de Cusco y departamento de Puno
No permite concluir: nada sobre provincias o distritos concretos: [...]
```

### 3.3 ✅ Mantener la biblioteca de datos

Procedimientos paso a paso: `guia_de_operacion.md` §3. Aquí, el mapa de comandos.

| Comando | Para qué | Cuándo | ¿Escribe? |
|---|---|---|---|
| `pap revisar [ID]` | Estado de las fuentes: estrategia, compuerta, capturas, días sin revisar; con ID, los pasos de descarga y pendientes | Antes de actualizar una fuente | No |
| `pap descargar ID` | Descarga si la receta es automática; si es manual, muestra los pasos | Al incorporar una fuente | Almacén |
| `pap registrar ID [archivos]` | Guarda en el almacén un archivo de la bandeja o los indicados (`--issued`, `--recurso`, `--nota`…) | Después de descargar a mano | Almacén |
| `pap verificar [ID] [--rapido]` | Recalcula huellas (o solo tamaños) | Después de registrar | `verificaciones.jsonl` |
| `pap citar CLAVE [--corta]` | Cita de una fuente (ID) o de un archivo (prefijo de huella) | Para citar | No |
| `pap construir {territorio,poblacion,puentes,gasto,endes,enaho,mapa_pobreza,indicadores}` | Reconstruye una tabla curada o estandarizada | Tras cambiar crudos o código | `biblioteca` |
| `pap calcular` | Reconstruye el cubo `fact_indicador.parquet` | Después de `construir` | `biblioteca` |
| `pap almacen comprimir [--dry-run]` | Comprime con zstd los textos grandes; `--dry-run` solo lista | Mantenimiento | Almacén (sin `--dry-run`) |
| `pap indice` | Reconstruye `indice.duckdb` | Tras registrar capturas | `biblioteca` |
| `pap recetas {generar,validar,sincronizar}` | Recetas de descarga desde el catálogo; `validar` las contrasta con el catálogo y R-DEP-01 | Al tocar el catálogo | `validar`: no |
| `pap validar-reglas [--carpeta casos_implementador]` | Corre los casos de prueba del validador de reglas | Al cambiar una regla | No |
| `pap foto-pim` | **Desactivada** (8/10/2026): `registrar` y `extraer` se niegan; `listar` y `vistas` funcionan | No usar | No |

**Orden de reconstrucción** (cada paso depende del anterior):

```text
construir territorio → poblacion → puentes → gasto → endes → enaho → mapa_pobreza → indicadores → calcular
```

Cuidados (detalle en `guia_de_operacion.md` §3.3):
- Usa exactamente los crudos fijados en `curados/insumos.lock.yaml`; para tomar capturas nuevas, `--actualizar-insumos`.
- Se niega a construir con código sin commit (`--permitir-sucio` deja el manifiesto «sucio») o si falla una prueba bloqueante (`--forzar`: no usarlo en producción).
- `construir poblacion` usa ~3,5 GB de RAM; `construir gasto` es el bloque más pesado.
- Con los mismos insumos y código, la huella del cubo debe repetirse: hoy es `ba1fbc55…`.
- Los crudos y los Parquet no están en git: respalda `biblioteca/cruda/almacen/`.

Consulta directa del cubo con SQL y edición de tablas curadas o reglas: `guia_de_operacion.md` §2.2, §3.4 y §3.5.

### 3.4 ✅ Calidad: pruebas, regresión y matriz

| Qué | Comando | Resultado esperado hoy |
|---|---|---|
| Todas las pruebas | `uv run pytest -q` | 748 pasan, 1 aviso (≈ 6 min) |
| Regresión Q1–Q4 (cifras, semáforos y confianza iguales a la referencia) | Incluida en `pytest`: `tests/test_regresion_q1_q4.py` | Verde |
| Matriz de cobertura reducida (60 casos) | `uv run python tests/matriz/correr.py --reducida --salida salidas/matriz` | 60 casos, 0 fallos |
| Matriz completa (≈ 5 000 casos, ~5 min) | `uv run python tests/matriz/correr.py --salida salidas/matriz --reporte backlog/slice-1/evidencia/matriz.md` | 5 086 casos, 0 errores, 0 fallos (sobrescribe el reporte del cierre: úsalo con otro nombre si no quieres perderlo) |
| Validador de reglas | `uv run pap validar-reglas` y `… --carpeta casos_implementador` | 535 y 448 casos ok; 68 reglas del alcance implementadas |

La matriz cuenta los casos por clase (respondida, no se puede, aclaración, error), tema e intención, y lista los fallos. Guía de las pruebas del piloto: `calidad.md`.

## 4. Casos de uso

Todos los ✅ se corrieron con `--salida` a una carpeta temporal. Se muestra el principio de la respuesta.

### 4.1 Disponibles hoy

| # | Quiero saber… | Comando (`uv run pap preguntar …`) | Qué vas a ver |
|---|---|---|---|
| 1 ✅ | ¿Cuánta anemia hay en Lima Metropolitana? (**nivel_actual**, Lima) | `--intencion nivel_actual --tema anemia --territorio Lima` → exit 2, y luego el mismo comando con `--elegir 1` | Primero: «Hay varios lugares llamados «Lima». ¿Cuál quieres? 1) Lima Metropolitana… 2) Lima Región… 3) Callao». Luego: «25,3 % … en Lima Metropolitana en 2025», confianza alta |
| 2 ✅ | ¿Cómo ha cambiado la anemia en Huancavelica? (**evolucion**, anemia) | `--intencion evolucion --tema anemia --territorio "departamento de Huancavelica"` | «No muestra un cambio estadísticamente claro…», 38,6 % en 2025 con la forma vigente; en «Más contexto», 53,5 % en 2015 y 54,5 % en 2025 con la forma anterior y 32,9 % en 2024 y 38,6 % en 2025 con la vigente |
| 3 ✅ | ¿Cuántos niños tienen anemia en Ayaviri? (distrito, **SIEN**) | `--intencion nivel_actual --tema anemia --territorio "Ayaviri, Melgar"` | «No se puede saber cuántos niños de Ayaviri tienen anemia…»; lo más cercano: ≈ 10 % (7 %–12 %) de 547 niños medidos en establecimientos. Confianza media |
| 4 ✅ | ¿Cuánta desnutrición crónica hay en Ayaviri? (**no se puede**, desnutrición) | `--intencion nivel_actual --tema desnutrición --territorio "Ayaviri, Melgar"` | «No podemos mostrar cuánto hay de desnutrición crónica en Ayaviri por distrito. Sí tenemos la cifra para el departamento de Puno». Sin cifra, exit 0 |
| 5 ✅ | ¿Qué departamento tiene más anemia? (**identificar_extremo**) | `--intencion identificar_extremo --tema anemia --nivel departamento` | «En 2025, Puno es el departamento con la anemia … más alta, con diferencia estadísticamente clara frente a los demás»: 56,1 % |
| 6 ✅ | ¿Es mayor la pobreza en Puno que en Cusco? (**comparacion**, pobreza, `--elegir 1,1`) | `--intencion comparacion --tema pobreza --territorio "Cusco" --comparar-con "Puno" --elegir 1,1` | «…mayor en Puno que en Cusco, con una diferencia estadísticamente clara»: 18,8 % frente a 37,5 % (2025). Sin `--elegir`: exit 2 y la aclaración de «Cusco». Con `--elegir 1` solo: pregunta por «Puno» |
| 7 ✅ | ¿Cuánto se gastó en salud y nutrición infantil en Puno? (**gasto**) | `--intencion nivel_actual --tema gasto --territorio "departamento de Puno"` | «S/ 132,1 millones … en 2025 … registrado por entidades con sede en Puno», con «No leas esta cifra como todo el gasto en Puno» |
| 8 ✅ | ¿Cómo evolucionó el gasto del país? (gasto, **serie**) | `--intencion evolucion --tema gasto --territorio "Perú" --desde 2023 --hasta 2025` | «En Perú, el gasto … pasó de S/ 2 263,9 millones en 2023 a S/ 2 455,9 millones en 2025, en soles de 2025: aumentó.» El monto registrado de 2023 (S/ 2 179,2 millones) y el factor del IPC van en «Para citar» |
| 9 ✅ | ¿Cuánta pobreza hay en Ayaviri? (**pobreza**, distrito) | `--intencion nivel_actual --tema pobreza --territorio "Ayaviri, Melgar"` | «Entre 23 % y 42 % … en Ayaviri en 2018» (estimación con modelo), confianza **baja** y «cuál es la situación hoy: el dato es de 2018» |
| 10 ✅ | ¿Y la pobreza de Puno entre 2024 y 2025? (`--desde/--hasta`) | `--intencion evolucion --tema pobreza --territorio "departamento de Puno" --desde 2024 --hasta 2025` | «…se mantuvo sin cambio estadísticamente claro»: 37,5 % en 2025 y 39,9 % en 2024 |
| 11 ✅ | ¿Cuánta anemia hubo en Puno en 2024? (`--anio`) | `--intencion nivel_actual --tema anemia --territorio "departamento de Puno" --anio 2024` | 53,1 % en 2024. Con `--anio 2019` y el país, «no se puede»: «No hay datos de anemia de 2019 con la forma de medir actual. La cifra de 2019 solo existe con la forma de medir anterior…», y ofrece la evolución hasta 2019 |
| 12 ✅ | ¿Cómo se ven juntos el gasto y la anemia en Puno? (**cruce**) | `--intencion cruce --tema gasto --territorio "departamento de Puno"` | «La cifra clave es el gasto en servicios de salud y nutrición infantil. La de la anemia … del mismo lugar está en «Más contexto». No muestran si una causa la otra.» Gasto, cobertura de tamizaje SIEN y anemia ENDES |
| 13 ✅ | ¿Sirvió el gasto contra la anemia en Puno? (**efecto**) | `--intencion efecto --tema anemia --territorio "departamento de Puno"` | «No se puede saber si el gasto contra la anemia sirvió en Puno: no encontramos una evaluación publicada», más lo que sí se sabe. Confianza media (respuesta parcial) |
| 14 ✅ | Preguntar sin saber el tema (**aclaración** de tema) | `--intencion nivel_actual --territorio Puno` | «¿De qué problema quieres saber? 1) Anemia 2) Desnutrición crónica 3) Gasto público en salud y nutrición infantil 4) Pobreza». Exit 2 |
| 15 ✅ | Preguntar por un tema que no está (educación) | `--intencion nivel_actual --tema educación --territorio Puno` | «Todavía no tenemos datos de ese tema» y los cuatro que sí. Exit 0 |
| 16 ✅ | Repetir las preguntas del piloto (Q1–Q4, **archivo JSON** y carpeta) | `curados/motor/consultas_minimas/q1.json` o `curados/motor/consultas_minimas/` | Las cuatro respuestas del piloto por el motor nuevo (Q1: Huancavelica; Q2: Ayaviri; Q3: efecto en San Juan de Lurigancho; Q4: el distrito más pobre) |
| 17 ✅ | Ver qué cifras armaría el motor, sin calcular (**--plan**) | `--intencion nivel_actual --tema anemia --territorio "departamento de Puno" --plan` | Un JSON con intención, tema, territorio, periodo y la lista de cifras. No escribe nada |
| 18 ✅ | Una cifra concreta, no un tema (**--indicador**) | `--intencion nivel_actual --indicador sien_anemia_tamizados_6_35m --territorio "Ayaviri, Melgar"` | La cifra del SIEN con su rótulo («en establecimientos…»), confianza media |
| 19 ✅ | El «más pobre» de un lugar (**límite de `--dentro-de`**) | `--intencion identificar_extremo --tema desnutrición --nivel departamento --dentro-de Puno --elegir 1` | «No podemos mostrar qué lugares tienen el valor más alto … dentro de Puno: el orden que calculamos es solo para todo el país». Ofrece el orden nacional |
| 20 ✅ | Citar la fuente de los datos de ENDES | `uv run pap citar INEI-ENDES --corta` | «INEI, Encuesta Demográfica y de Salud Familiar, ENDES 2025 (código 1038) … Consultado el 07-oct-2026.» |
| 21 ✅ | Saber qué fuentes tengo y cuáles están al día | `uv run pap revisar` | Una tabla: fuente, estrategia, compuerta, capturas, días sin revisar |

**Una pregunta ambigua se resuelve así:** el comando imprime las opciones y sale con 2; repites **el mismo comando** agregando `--elegir N`.

### 4.2 Pendientes (comando o interfaz por definir)

| # | Quiero… | Qué vas a poder hacer | Slice |
|---|---|---|---|
| P1 ⏳ | Escribir la pregunta con mis palabras («¿Cuánta anemia hay en Puno?») | Un LLM la traduce a la consulta estructurada; nunca calcula ni ve cifras (P-01). Lo que no entiende o está fuera de alcance se responde con una aclaración o con «todavía no tenemos datos de eso». Comando o interfaz por definir | 2 |
| P2 ⏳ | Que me repregunte cuando mi texto es confuso | Aclaración en lenguaje libre, con reintento si la consulta no valida. Comando o interfaz por definir | 2 |
| P3 ⏳ | Preguntar desde el celular | Una caja de pregunta y la respuesta por capas como desplegables (visible, «Más contexto», «Para citar»), con la versión de la biblioteca y enlaces a las fuentes oficiales. Interfaz por definir | 3 |
| P4 ⏳ | Usar el servicio desde otro programa | Una API sobre el cubo precalculado, con respuesta en < 2 s. Interfaz por definir (el plan menciona FastAPI + DuckDB en solo lectura) | 3 |
| P5 ⏳ | Que la web sea accesible | Accesibilidad WCAG AA, confianza sin colores | 3 |
| P6 ⏳ | Probar el servicio con un grupo pequeño de personas | Beta cerrada en la nube, con medición de uso sin datos personales | 4 |
| P7 ⏳ | Preguntar por temas nuevos (más allá de anemia, desnutrición, pobreza y gasto) | Un tema nuevo por sub-slice: fuente aprobada → indicador con doradas → intenciones → web. Comando o interfaz por definir | 5 |

## 5. Qué NO hace (todavía)

| Límite | Detalle |
|---|---|
| ⏳ **Sin lenguaje libre** | No hay LLM en el motor (slice 2). La pregunta se arma con opciones o con un JSON |
| ⏳ **Sin web ni API** | Todo es por Terminal (slice 3) |
| **Solo 9 indicadores** | Los de §3.1: anemia (4), desnutrición crónica (1), pobreza (2) y gasto (2). Otro tema, un «no se puede» |
| **Niveles y años con datos limitados** | Desnutrición y pobreza ENAHO: no hay provincia ni distrito (pobreza distrital: solo el Mapa de 2018, con rango). Anemia ENDES: sin provincia ni distrito; por distrito solo el SIEN 2025. Gasto: provincia y distrito solo con gasto municipal y obras ubicadas |
| **Sin preguntas «dentro de»** | «El más alto dentro de Puno» responde «no se puede»: los rankings son nacionales (`planificador.extremo_dentro_de`: `solo_nacional`) |
| **Sin ranking de gasto** | R-GASTO-13 |
| **Cruces solo CR-01** | Gasto × anemia ENDES vigente. Los demás cruces se dan como cifras separadas |
| **La evolución del gasto compara en soles de 2025** | Para comparar años, los montos se ajustan por inflación con el IPC de Lima del último año cerrado (G-01, R-GASTO-12; adenda S1-12). La respuesta no da la diferencia ni el porcentaje de cambio, solo si aumentó o disminuyó. Una cifra de un solo año sigue en soles de ese año |
| **Sin descargas nuevas** | Agregar fuentes o datos es trabajo aparte (F-04) |

### Pendientes del dueño detrás de un parámetro

Se resuelven editando una línea de `curados/motor/parametros_motor.yaml` (sección `pendientes_dueno`) cuando el dueño decida. Detalle: `decisiones.md`, «Decisiones pendientes del dueño».

| ID | Qué hay que decidir | Valor de hoy | Recomendado |
|---|---|---|---|
| X-02 | ¿«¿Cuántos?» del SIEN da también el conteo (52 de 547 niños medidos)? | **No** (`mostrar_conteo_sien: false`) | Sí, como tarjeta de la capa 2 |
| X-03 | ¿CR-01 muestra también el gasto del mismo año que la anemia comparada? | **No** (`cr01_mismo_anio: false`) | Sí |
| X-04 | ¿Se muestran los dos intervalos o solo uno? | Los dos (el propio y el del INEI) en la ficha | Uno visible; los dos en la ficha técnica. Pesa en el slice 3 |
| X-01 | Aprobar el texto de «¿Qué puedo hacer?» | Se muestra «pendiente de revisión» | Revisarlo y poner `revisado_dueno: true` |

Siguen abiertas, sin parámetro asociado en el slice 1: X-05 (revisar lo provisional antes de la beta), X-06 (separar ejecutoras mixtas antes de la Ola 1), X-07 (listas curadas sin revisar) y X-08 (solicitudes por la Ley 27806).

## 6. Hoja de ruta

| Slice | Qué podrá hacer el usuario al terminar | Estado |
|---|---|---|
| **1. Motor por intenciones** | Cualquier pregunta estructurada sobre los 9 indicadores, por capas y validada; el motor pregunta si hay ambigüedad. La adenda agrega la evolución del gasto en soles constantes y corrige textos de evolución, cruce y efecto | ✅ cerrado el 3/11/2026; adenda cerrada el 4/11/2026 |
| **2. Intérprete de preguntas** | Escribir la pregunta en lenguaje natural; un LLM la traduce a la consulta del slice 1. Antes, decisión del dueño sobre proveedor, presupuesto y qué se guarda de las preguntas (P-03) | ⏳ |
| **3. API y web mínima** | Usarlo desde el celular: caja de pregunta, capas, versión de la biblioteca y enlaces oficiales. Antes, X-04 | ⏳ |
| **4. Beta cerrada** | Un grupo pequeño de personas lo usa en la nube. Antes: prueba con usuarios (P-05), revisión de lo provisional (X-05), despliegue (F-05) y medición sin datos personales (P-03) | ⏳ |
| **5. Ampliación de datos (Ola 1)** | Preguntar por temas nuevos, uno por sub-slice. Antes: GA-13 y X-06 | ⏳ |

Las observaciones del cierre del slice 1 (el cruce que prometía cifras «lado a lado», la evolución que no mostraba el año con el que compara, la frase de efecto que se contradecía y la evolución del gasto que no comparaba años) se resolvieron en la adenda (`backlog/slice-1/evidencia/cierre.md`, sección «Adenda»). Las observaciones bajas que cambian el patrón de Q1–Q4 (H14, H15, H17, H18, H21 y A-H8) se revisan en el slice 3, con la web ⏳.

## 7. Problemas frecuentes

| Síntoma | Qué significa y qué hacer |
|---|---|
| «Hay varios lugares llamados «X». ¿Cuál quieres?» (exit 2) | No es un error: el lugar es ambiguo. Repite **el mismo comando** con `--elegir N`. Con «Lima» las opciones son Lima Metropolitana, Lima Región y Callao |
| «¿De qué problema quieres saber?» (exit 2) | Falta `--tema` (o `--indicador`). Repite con uno de los cuatro temas |
| «No encontramos ese lugar… Escribe el lugar de nuevo» (exit 2) | No hay opciones para elegir: corrige el nombre. `--elegir` no ayuda aquí |
| `✘ La opción N no existe. Elige un número entre 1 y 3.` (exit 1) | `--elegir` fuera de rango: usa un número de la lista |
| Con dos lugares ambiguos, el comando vuelve a preguntar tras `--elegir 1` | Pasa un número por lugar: `--elegir 1,1`, en el orden `--territorio`, `--comparar-con` |
| «✘ Falta el lugar: ¿de qué departamento, provincia o distrito?» (exit 1) | Falta `--territorio` (salvo en `identificar_extremo`) |
| «✘ No encontramos «archivo.json»» (exit 1) | Revisa la ruta; las consultas mínimas están en `curados/motor/consultas_minimas/` |
| Exit 2 con el texto de uso (argparse) | Un valor de `--intencion` o `--nivel` que no existe. Mira `uv run pap preguntar --help` |
| La respuesta es «no se puede» | No es un fallo (exit 0): los datos o las reglas no permiten responder. Lee «Lo más cercano que sí tenemos»: otro año, el nivel superior o el distrito de origen |
| «No hay datos de … de 2019 con la forma de medir actual» | La anemia con la forma vigente solo existe 2024–2025; la anterior, 2015–2025. Pregunta por un año con datos |
| `pap construir` o `pap calcular` dice «El código tiene cambios sin commit» | Haz commit antes: los manifiestos citan el commit. `--permitir-sucio` solo para pruebas, deja el manifiesto marcado |
| La huella del cubo no es `ba1fbc55…` | Revisa `uv sync` y la versión del commit; si persiste, avisa: es un problema de reproducibilidad |
| Una dorada falla al construir | La cifra del INEI no se reproduce: revisa definición, criterio y página citada. No uses `--forzar` |
| No puedes descargar de `.gob.pe` | Descarga con el navegador a `biblioteca/cruda/bandeja/<ID>/` y luego `pap registrar` |

Más problemas de entorno (git, memoria, disco): `guia_de_operacion.md` §5.

## 8. Dónde encontrar más

| Necesito… | Documento |
|---|---|
| Preparar el entorno, mantener datos, cambiar tablas o reglas | [guia_de_operacion.md](guia_de_operacion.md) |
| Cómo debe verse una respuesta (capas, redacción, tipos) | [especificaciones/contrato_respuesta.md](especificaciones/contrato_respuesta.md) |
| Cómo está construido | [arquitectura.md](arquitectura.md) |
| Cómo comprobar el piloto | [calidad.md](calidad.md) |
| Qué está decidido y qué espera al dueño | [decisiones.md](decisiones.md) |
| Valores por defecto del motor | `curados/motor/parametros_motor.yaml` |
| Qué cifras arma cada intención | `curados/motor/intenciones.yaml` |
| Plan de slices y backlog | `backlog/plan_slices.md`, `backlog/README.md` |
| Cierre del slice 1 y supuestos aplicados | `backlog/slice-1/evidencia/cierre.md`, `backlog/slice-1/consultas_al_dueno.md` |
| Foto del proyecto | [estado.md](estado.md) |

Ayuda de cada comando: `uv run pap --help` y `uv run pap <comando> --help`.
