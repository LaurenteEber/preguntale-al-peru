# Pregúntale al Perú — Arquitectura y funcionamiento

Versión al 4/11/2026 (slice 1 y su adenda cerrados, etiqueta git `slice-1-adenda-cerrada`; las etiquetas `slice-1-cerrado` y `piloto-cerrado` son de la carpeta de trabajo anterior y no existen en este repositorio, `docs/historia.md`). Estado vivo: `docs/estado.md`.

## 1. Qué es

Una web donde cualquier persona hace una pregunta sobre un problema del país («¿cómo evolucionó la anemia en Huancavelica?») y recibe una respuesta calculada con fuentes públicas oficiales (INEI, MEF, INS…), por territorio, con los límites de cada cifra a la vista.

**Hoy existe** la maquinaria completa de punta a punta para el **piloto**:
- datos crudos trazables;
- tablas curadas;
- un cubo de indicadores;
- un validador de reglas de publicación;
- un motor por intenciones que responde cualquier pregunta **estructurada** sobre los 9 indicadores (cualquier territorio y año con datos) con texto por plantilla, entregado **por capas** (contrato de respuesta, §4.9). Q1–Q4 son ahora su regresión;
- cuando no se puede responder, una respuesta de «no se puede» o una aclaración (§4.8).

**Todavía no existen** la web ni el intérprete de preguntas con LLM (hoy la consulta se escribe con opciones de la CLI o en JSON). Son los slices 2 y 3 de la fase 5.

## 2. Principios de diseño

| Principio | Cómo se cumple |
|---|---|
| **Toda cifra es trazable** hasta el archivo crudo exacto | Almacén por huella SHA-256, `datapackage.json` por captura, manifiestos con la huella de cada insumo y del código (commit) |
| **Mismo crudo → mismas cifras** | Parquet ordenado por clave, estimaciones redondeadas a 8 decimales, versiones fijadas en `uv.lock`, construcción rechazada si el código tiene cambios sin commit |
| **No se publica nada que las reglas no permitan** | 96 reglas de publicación y atribución (68 en el validador del piloto), aplicadas a cada cifra y a cada respuesta |
| **Solo fuentes oficiales** | Las cifras de referencia («doradas») citan documentos oficiales: del INEI y, para el SIEN, del INS. Una prueba falla si aparece otra cita (decisiones del 11 y 12/10/2026) |
| **Validado contra lo publicado** | El cubo debe reproducir las cifras doradas del INEI (±0,1 pp) o no se construye |
| **Independencia** | Cada pieza importante pasó por analistas, auditores y verificadores que no la construyeron (registro en `docs/historia.md`) |
| **Mantenible por una persona** | Python + SQL, sin servidores: DuckDB, Parquet y una CLI propia (`pap`) |

## 3. Vista general del flujo

```
 Catálogo de fuentes (catalogo)
        │  olas y compuerta de ingesta
        ▼
 Capa cruda (biblioteca/cruda)  ← pap descargar / pap registrar / pap verificar
        │  crudos inmutables por huella + datapackage.json + verificaciones.jsonl
        ▼
 Capa 0 y estandarizada (biblioteca/dimensiones, /estandarizada)  ← pap construir …
        │  territorio, población, puentes, gasto, encuestas, Mapa de Pobreza
        ▼
 Tablas curadas del piloto (curados/capa0 → dimensiones)  ← pap construir indicadores
        │  dim_indicador, cruces_permitidos, cifras_doradas, grupos_oficiales_inei
        ▼
 Cubo de indicadores (biblioteca/indicadores/fact_indicador.parquet)  ← pap calcular
        │  39 539 filas: cifra, EE, CV, IC, n, avisos, validada_dorada
        ▼
 Motor por intenciones + validador de reglas  ← pap preguntar (opciones, consulta mínima .json o carpeta)
        │  consulta mínima → resolver territorial → planificador de cifras → cifras → validador
        │  (etapas 0–7) → plantilla por intención → validador de la respuesta (etapas 8–10) →
        │  ficha de límites → capas  (o «no se puede» / aclaración)
        ▼
 Respuesta por capas (salidas/preguntar/<id>.json y .md; la carpeta no va a git)
```

## 4. Componentes

### 4.1 Catálogo y priorización (`catalogo/`)
- **Catálogo v2:** 418 fuentes con esquema, estrategia de descarga y compuerta («aprobada» por prueba de humo o por captura verificada).
- **Olas:** Ola 0 (referencia, denominadores y puentes: 19 fuentes) y Ola 1 (núcleo: 29 fuentes).
- **Regenerar:** `just catalogo` o `catalogo/scripts/`. `catalogo/inferencia_verificada.csv` declara, por fuente × año, hasta qué nivel territorial infiere cada encuesta.

### 4.2 Capa cruda (`biblioteca/cruda/`)
Toda obtención termina igual:

**archivo → huella SHA-256 → validación de forma → almacén → `datapackage.json` → registro de verificaciones → índice DuckDB.**

| Pieza | Ubicación | ¿En git? |
|---|---|---|
| Recetas (cómo se obtiene cada fuente) | `curados/recetas/<ID>.yaml` | sí |
| Crudos inmutables (por huella; texto > 10 MB comprimido `.zst`) | `cruda/almacen/sha256/aa/bb/<huella>` | **no**: necesitan respaldo externo |
| Capturas (metadatos Frictionless v2 + DCAT/PROV) | `cruda/capturas/<ID>/<fecha>/datapackage.json` | sí |
| Bitácora de verificaciones | `cruda/verificaciones.jsonl` | sí |
| Bandeja de entrada (descargas manuales) | `cruda/bandeja/<ID>/` | no |
| Índice consultable | `cruda/indice.duckdb` (derivado, se reconstruye) | no |

Las descargas de dominios `.gob.pe` solo funcionan desde la laptop del dueño, con el navegador. El archivo queda en Descargas o en la bandeja y `pap registrar` lo incorpora.

### 4.3 Capa 0 y estandarizada (`biblioteca/dimensiones/`, `estandarizada/`)
Se construye con `pap construir <bloque>`. Cada bloque escribe Parquet ordenado, un **manifiesto** (huellas de insumos, código y salidas) y un archivo de **pruebas** bloqueantes.

| Bloque | Tablas principales |
|---|---|
| `territorio` | `dim_ubigeo_historico` (1 893 distritos vigentes, versiones e historia), `puente_ubigeo` INEI–RENIEC, `dim_ambito` (Lima Metropolitana, Lima Región, Callao…), `dim_dominio` |
| `poblacion` | `fact_poblacion` (oficial, censada y prorrateo propio IPF por edad simple), `fact_poblacion_grupo` (6–35 m y otros grupos en meses) |
| `puentes` | `dim_ipc` (BCRP), `dim_establecimiento_salud` (RENIPRESS) |
| `gasto` | `fact_gasto_territorial` (MEF 2023–2025, ~6,8 M filas), `dim_unidad_ejecutora`, `dim_inversion_ubicacion`, `dim_tema_gasto` y la capa de trazabilidad de programas |
| `endes`, `enaho`, `mapa_pobreza` | `endes_nino` (2015–2025), `enaho_sumaria` (2024–2025), `fact_mapa_pobreza` (2018) |

**Fijación de insumos:** `curados/insumos.lock.yaml` dice qué captura exacta usa cada construcción. `--actualizar-insumos` lo reescribe con las capturas más recientes.

**Guardia del gasto:** el gasto solo se lee por las vistas de `vistas_gasto.sql` y `gasto_tema('<tema>')`. `guardia_gasto.py` rechaza cualquier otra consulta (R-GASTO-05).

### 4.4 Tablas curadas del piloto (`curados/capa0/`)
Son la fuente de verdad editable (YAML/CSV en git); `pap construir indicadores` las valida y las publica como Parquet.

| Archivo | Qué contiene |
|---|---|
| `dim_indicador.yaml` | Los 9 indicadores del piloto con todos sus metadatos (definición, criterio, niveles válidos, quiebres, rótulos, diseño muestral) |
| `cruces_permitidos.yaml` | Lista blanca de cruces entre indicadores (CR-01: gasto ex-PAN × anemia) |
| `cifras_doradas.csv` | 206 cifras oficiales con cita (documento, URL, cuadro y página); 89 bloqueantes. 176 del INEI, validadas a ciegas contra el PDF (11/10/2026), y 30 del SIEN del INS (`oficial_ins`, `control_registro`; 12/10/2026) |
| `grupos_oficiales_inei.csv` | Grupos de departamentos estadísticamente semejantes publicados por el INEI (pobreza 2024–2025) |
| `definiciones_endes.yaml`, `cifras_control_inei.yaml`, `ejecutoras_alcance.yaml`, `lista_transferencias.yaml`, … | Definiciones y listas revisadas por el dueño |

**Indicadores del piloto**

| id | Qué mide | Fuente | Años |
|---|---|---|---|
| `endes_anemia_6_35m` | Anemia 6–35 meses, forma de medir anterior (RM 363-2022) | ENDES | 2015–2025 |
| `endes_anemia_6_35m_oms2024` | Anemia 6–35 meses, forma de medir vigente (RM 251-2024) | ENDES | 2024–2025 |
| `endes_dci_menores_5` | Desnutrición crónica < 5 años | ENDES | 2015–2025 |
| `sien_anemia_tamizados_6_35m` | Anemia en niños tamizados en establecimientos | SIEN (INS) | 2025 |
| `sien_cobertura_tamizaje_6_35m` | Cobertura de tamizaje (dos cotas) | SIEN | 2025 |
| `gasto_ex_pan`, `gasto_ex_pan_opcion_c` | Gasto en servicios que antes eran del PAN | MEF | 2023–2025 |
| `enaho_pobreza_monetaria` | Pobreza monetaria | ENAHO | 2024–2025 |
| `mapa_pobreza_2018` | Pobreza distrital (estimación con modelo, solo intervalo) | INEI | 2018 |

### 4.5 Cubo de indicadores (`pap calcular`)
`fact_indicador.parquet` tiene una fila por indicador × año × nivel × territorio × medida × línea.

**Métodos estadísticos**
- **Encuestas:** svy con el diseño complejo (Taylor), IC **Korn-Graubard** (variante NCHS), años y estratos según R-ENC-10.
- **SIEN:** Wilson y dos cotas.
- **Gasto:** suma por `gasto_tema` con la guardia del gasto.
- **Gasto en soles constantes (desde la versión 1.2.0 del cubo, S1-12):** cada fila `devengado` tiene su fila `devengado_constante` = devengado × factor, con `anio_base_deflactor` y `factor_deflactor`. Año base: el mayor año con el IPC completo y con gasto (hoy 2025); factor: `ipc_prom_anual(base) / ipc_prom_anual(año)` de `dim_ipc` (BCRP PN38705PM). El PIM y el PIA no se deflactan. El motor usa estas filas solo para comparar años (R-GASTO-12).
- **Mapa 2018:** el intervalo publicado.

**Pruebas que debe pasar el cubo**
- **CAL-03:** reproduce todas las doradas bloqueantes.
- **CAL-07 y CAL-08:** los controles del gasto y la conservación R-GASTO-01 dan exacto.
- **CAL-11:** cada fila `devengado` del gasto hasta el año base tiene su fila `devengado_constante`, con valor = devengado × factor.
- **CAL-10:** el SIEN reproduce las cifras oficiales del INS (casos y evaluados exactos: nacional, 24 departamentos y Callao, Lima Región, Ayaviri y San Juan de Lurigancho).

**Huella actual:** `sha256:010ea965…` (desde el 4/11/2026, adenda S1-12: soles constantes; la anterior, `ba1fbc55…`, es la del release `biblioteca-ba1fbc55`). Debe ser idéntica en macOS y Linux: en la nube se reproduce con `pap calcular` después de bajar el release.

### 4.6 Reglas de publicación (`reglas/`)
- **Contenido:** 96 reglas vigentes (93 del MVP) en 11 etapas:
  - 0 prerrequisitos
  - 1 territorio
  - 2 nivel
  - 3 denominador
  - 4 precisión
  - 5 series
  - 6 divulgación
  - 7 semáforo de la cifra
  - 8 cruces
  - 9 semáforo de la respuesta
  - 10 comunicación
- **Ficha de límites y lenguaje:** `ficha_limites_y_lenguaje.md`.
- **`reglas.json` y `reglas.md` son generados: nunca se editan a mano.** `reglas/consolidador/consolida_reglas.py` los genera a partir de las propuestas, las correcciones de la prueba y de las auditorías, y las decisiones del dueño (`ajustes_dueno.py`).
- **El consolidador se detiene** si falla una prueba de consistencia o si un ajuste pisa un campo ya corregido.

### 4.7 Validador (`src/pap/motor/validador/`)
- **Qué es:** 68 reglas como funciones puras. Cada una devuelve resultados con `accion`, `motivo`, `detalle`, `mensaje` y `objetivo`: publicar, rotular, advertir, suprimir, bloquear el cruce, revisión humana…
- **Precedencia y degradación:**
  - la precedencia entre reglas sigue R-MOTOR-02;
  - con la degradación (R-MOTOR-01), si una cifra no es publicable a un nivel, se intenta un nivel o periodo más grueso.
- **Etapas:**
  - **0–7, por cifra:** terminan en su semáforo (R-CRUCES-09: verde, ámbar, rojo o no publicable).
  - **8–10, por respuesta:** cruces, pruebas de cambio (R-ENC-11), semáforo de la respuesta (R-CRUCES-10) y corrector de lenguaje (R-LENGUAJE-02/03/06).
- **Casos de prueba:** `tests/casos_validador/casos/` (535, de un analista independiente) y `tests/casos_validador/casos_implementador/` (448).

### 4.8 Motor por intenciones (`src/pap/motor/`)
Desde el slice 1 (3/11/2026) la persona ya no escribe las cifras ni la plantilla: solo lo que pregunta (intención, tema, lugar, año). El resto se decide por datos.

**Flujo de una pregunta**
1. **Consulta mínima** (`consulta.py`, esquema `curados/motor/esquemas/consulta_minima.schema.json`): intención, tema o indicador, lugar y periodo. No trae cifras. Los errores salen en lenguaje sencillo (`textos/errores_consulta.yaml`).
2. **Resolver territorial** (`territorio.py`): convierte el texto del lugar en un territorio vigente, o en una aclaración si es ambiguo (homónimos, Lima en tres ámbitos). Sin red ni LLM.
3. **Planificador de cifras** (`planificador.py`): con `curados/motor/intenciones.yaml` (qué cifras pide cada tema × intención, con la decisión que lo exige) y los metadatos de `dim_indicador` y `cruces_permitidos`, arma el plan: las cifras, sus roles y las comparaciones. No hay reglas de ningún tema en el código Python.
4. **Cifras y validador** (`respuesta.py`): cada cifra se busca en el cubo y pasa por el validador (etapas 0–7); si hace falta, se degrada a otro nivel o periodo.
5. **Plantilla por intención** (`plantillas.py`): cinco plantillas genéricas (`nivel_actual`, `evolucion`, `comparacion`, `identificar_extremo`, `cruce_efecto`) redactan el borrador con textos fijos de `curados/motor/textos/plantillas/` y `bloques.yaml`. Los números entran solo por marcadores: `{{c:}}` cifra, `{{v:}}` verbo de cambio, `{{u:}}` universo, `{{e:}}` entidad y `{{p:}}` texto protegido.
6. **Validador de la respuesta** (etapas 8–10): si R-ENC-11 bloquea una comparación, se rehace el borrador (hasta 3 veces).
7. **Capas** (`capas.py`) y **ficha** (`ficha.py`): se generan el texto final con los números insertados al final, la ficha de límites y la respuesta por capas.

`preguntar.py` une los pasos 1–7 (`preguntar_minima`), y es el mismo camino que usan la CLI y la matriz de cobertura.

**Precios del gasto (adenda, S1-12).** Una comparación de gasto entre años pide `devengado_constante` (planificador) y llega al validador con `precios = constantes`, `anio_base_deflactor` y `factores_deflactor`, como pide R-GASTO-12; la cifra del año con el que se compara lleva la otra como `serie`. Una cifra de un solo año sigue en soles corrientes. La capa 1 dice «pasó de X en 2023 a Y en 2025, en soles de 2025: aumentó» (verbos dentro de `{{v:}}`, sin diferencia ni porcentaje) y la cita da el monto registrado de cada año y el factor.

**Evolución (adenda, S1-13).** «Más contexto» da la cifra del año con el que se compara (AD-1). Si el periodo pedido deja a la forma vigente de la anemia sin dos años, se cuenta la serie de la forma anterior (`intenciones.yaml`, `sin_serie_vigente`; E-06).

| Archivo | Papel |
|---|---|
| `consulta.py` | Carga y valida la consulta mínima |
| `territorio.py` | Resolver territorial determinista y aclaraciones de lugar |
| `planificador.py` | Plan de cifras a partir de `intenciones.yaml` |
| `preguntar.py` | Orquesta consulta → territorio → plan → respuesta; produce también «no se puede» y aclaración |
| `respuesta.py` | Busca las cifras en el cubo, el intervalo del INEI (`ic_inei`) y el contraste oficial (`contraste_oficial`) en las doradas, los grupos oficiales y el nombre completo de los distritos; corre el validador |
| `plantillas.py` | Las cinco plantillas genéricas; devuelven las piezas del contrato (`corta`, `clave`, `ojo`, `contexto`, `glosario`, `tema`). Los nombres de las plantillas del piloto (`q1_evolucion`…) se traducen a la genérica de su intención (`plantillas.nombres_antiguos`) |
| `capas.py` | Arma la respuesta por capas (§4.9): cifra clave con su fuente, confianza sin colores, avisos reescritos como «no concluyas…», una cita por cifra, glosario y «¿Qué puedo hacer?». No calcula ni decide reglas |
| `ficha.py` | La ficha corta (4 líneas: «Confianza en los datos», fuentes, territorio y «no permite concluir») y la ficha larga por cifra: origen, territorio, qué mide, precisión con los **dos intervalos**, método y contraste oficial del mismo criterio, con su entidad (INEI o INS). También el `.md` por capas |
| `formato.py` | Números y porcentajes, redondeo y traducción de códigos internos a lenguaje ciudadano |
| `calculo.py` | El cubo (`pap calcular`) |

**Datos del motor** (editables, sin tocar Python)

| Archivo | Qué contiene |
|---|---|
| `curados/motor/intenciones.yaml` | Qué cifras pide cada intención sobre cada tema, con la decisión que lo exige |
| `curados/motor/parametros_motor.yaml` | Valores por defecto del motor; cada entrada dice si es `decision:`, `pendiente:` o `supuesto:`. El bloque `pendientes_dueno` guarda X-02, X-03 y X-04 en su valor de hoy |
| `curados/motor/textos/` | Todo lo que la persona lee: `plantillas/<intención>.yaml`, `bloques.yaml`, `capas.yaml`, `no_se_puede.yaml`, `territorio.yaml`, `errores_consulta.yaml`, `cli.yaml`, `glosario.yaml`, `que_hacer.yaml` |
| `curados/motor/consultas_minimas/` | Q1–Q4 como consultas mínimas (JSON): la regresión del slice |
| `tests/fixtures/consultas_piloto/` | Las consultas q1–q4 del piloto (YAML), archivadas; siguen funcionando con `pap preguntar` |

**«No se puede».** Cuando los datos no permiten responder (año sin datos, nivel no válido, precisión o privacidad insuficientes, distrito creado después del año pedido, tema fuera del piloto, cruce fuera de la lista blanca…), la respuesta sale por las mismas capas pero **sin ninguna cifra**: la respuesta corta dice primero lo que no se puede (máximo `no_se_puede.respuesta_corta_max_oraciones` oraciones), «Lo más cercano que sí tenemos» ofrece solo una alternativa que el validador deja publicar, y el motivo va en «Más contexto». Si solo falta una parte, se responde y se dice lo que falta (respuesta parcial, R-LENGUAJE-05). Textos: `textos/no_se_puede.yaml`.

**Aclaración.** Si el lugar es ambiguo («Huancavelica» es departamento, provincia y distrito; «Lima»: Lima Metropolitana, Lima Región o Callao) o falta el tema, el motor no responde: devuelve una pregunta con opciones numeradas (T-03, R-TERRITORIO-09). No lleva cifras ni capas; la CLI sale con código 2 y se responde con `--elegir`.

**Matriz de cobertura.** `tests/matriz/` genera consultas mínimas para los 4 temas × intenciones × territorios (una muestra reproducible, semilla en `parametros_motor.yaml`) y comprueba que ninguna cae, que no queden marcadores ni códigos internos, que la capa 1 no pase del máximo de palabras y que toda combinación sin datos dé «no se puede» con su motivo. La corrida completa (5 086 casos, 0 fallos) está en `backlog/slice-1/evidencia/matriz.md`; en pytest corre una versión reducida (`matriz_cobertura.casos_pytest`).

**Preguntas en texto libre** (slice 2): las responde el intérprete (abajo), que solo produce la consulta mínima; el motor no cambia.

#### Intérprete de preguntas (`src/pap/interprete/`, slice 2)

`pap preguntar --texto "…"` → `interpretar()`:

1. **Limpieza** (`limpiar.py`, P-03): recorte a 1 000 caracteres, sin caracteres de control y sin números con forma de DNI,
   RUC o celular ni correos (`interprete.datos_personales`). Pasa antes del LLM, de la caché, del registro y de
   `pregunta_original`.
2. **LLM** (`llm.py`, P-07): Claude Sonnet 5.5 con esfuerzo bajo, por HTTP (httpx), con las instrucciones armadas desde datos
   curados (`prompt.py`: `curados/interprete/prompt.md`, `ejemplos.yaml`, el vocabulario y el esquema). La pregunta va como
   dato delimitado, fuera de las instrucciones. El LLM **no ve cifras** y solo devuelve una interpretación: consulta,
   aclaración, fuera de alcance, no es pregunta u otro idioma (`curados/motor/esquemas/interpretacion.schema.json`).
   - **Frontera:** la clave sale de `PAP_ANTHROPIC_API_KEY` solo en el momento de la llamada; 401/403 detienen el cliente,
     429/5xx tienen un reintento y el límite de gasto agotado da «no disponible». Toda falla termina en un mensaje fijo que
     ofrece las opciones. La API no acepta el esquema como salida estructurada (E-03): el código valida y reintenta una vez.
3. **Validación y anclas** (`interpretar.py`): esquema completo de S2-01 y, por cada valor, su ancla literal en la pregunta.
   Lo que no tiene ancla se descarta; lo que falta (lugar, intención, año, también un año relativo que el LLM omitió) lo
   completa un default o una aclaración **armada por el código**.
4. **Motor:** `preguntar_minima(consulta + pregunta_original)` del slice 1, sin cambios. «Entendimos…» es un texto fijo
   armado desde la consulta resuelta (`textos/interprete.yaml`).

**Grabaciones** (`tests/interprete/grabaciones/`): una por (pregunta limpia, modelo, `version_prompt`, error del reintento),
solo con el cuerpo de la respuesta y sus metadatos. pytest solo las reproduce (nunca llama a la red ni lee la clave);
`tests/interprete/evaluar.py` las graba (`--grabar`) y corre el conjunto de evaluación (`--evaluar`). Caché de 24 h en
`salidas/interprete/cache/` y registro de uso sin texto en `salidas/interprete/uso.jsonl` (fuera de git).

### 4.9 Contrato de respuesta por capas (12/10/2026)
Especificación: `docs/especificaciones/contrato_respuesta.md` (incluye los tipos `no_se_puede` y `aclaracion`).

| Capa | Contenido |
|---|---|
| 1. Visible (≈ 100 palabras; máximo 125) | Respuesta corta a la pregunta literal (si no se puede, se dice primero) · una cifra clave · «Ojo al leer» (qué **no** concluir) · «Confianza en los datos: alta / media / baja» · «¿Qué puedo hacer?» (solo texto oficial) |
| 2. Más contexto | Cifras secundarias en tarjetas con la etiqueta «no se compara» · avisos de las reglas · límites |
| 3. Para citar y verificar | Una cita por cifra (documento oficial si hay dorada) · glosario |
| Detalle técnico | Tabla de cifras, semáforo interno, ficha larga, reglas aplicadas, texto con marcadores |

- **Validación:** el validador revisa todo el texto visible (corta + clave + «Ojo» + contexto).
- **Textos fijos:** `curados/motor/textos/glosario.yaml` y `que_hacer.yaml`, este último con `revisado_dueno`.
- **Semáforo:** el interno (verde, ámbar, rojo) se muestra como confianza alta, media o baja.
- **Verificación:** la hizo un revisor independiente de usuario (anterior al repositorio; ver `docs/historia.md`).

## 5. Mapa del repositorio

| Carpeta | Contenido |
|---|---|
| `docs/` | Documentación vigente: **decisiones del dueño** (`decisiones.md`), estado, hoja de ruta, manual, esta arquitectura, especificaciones (`especificaciones/`) y guías (`guias/`); `historia.md` explica las citas a documentos anteriores al repositorio |
| `catalogo/` | Catálogo de fuentes, embudo de priorización y auditoría del catálogo (`salidas/`) |
| `curados/generadores/` | Scripts que generaron tablas curadas (gasto E3/P3, doradas del SIEN), con sus insumos de revisión |
| `reglas/` | Reglas (generadas: `reglas.json`, `reglas.md`, ficha y especificaciones de capa 0), su generador y sus verificaciones (`consolidador/`, `consolidador/pruebas/`), propuestas y alcance del piloto |
| `biblioteca/` | Datos: cruda, dimensiones, estandarizada, indicadores (los Parquet y los crudos no van a git) |
| `src/pap/` | La CLI `pap`: `cli.py`, ingesta (`registrar`, `descargar`, `verificar`, `citar`, `almacen`, `indice`, `recetas`), `capa0/` (construcciones) y `motor/` (cálculo, validador, respuesta) |
| `tests/` | 748 pruebas automáticas (pytest) |
| `curados/capa0/` | Tablas curadas editables (fuente de verdad) |
| `curados/motor/` | Catálogo de intenciones, parámetros, consultas mínimas, esquemas y textos fijos (`textos/`); las consultas del piloto archivadas y los casos del validador están en `tests/fixtures/consultas_piloto/` y `tests/casos_validador/` |
| `backlog/` | Plan por slices (`plan_slices.md`) y el slice 1 con su evidencia (`backlog/slice-1/evidencia/`) |
| `salidas/` | Respuestas que escribe `pap preguntar` (no va a git) |
| `catalogo/scripts/` | Generador del catálogo |

## 6. Stack

- **Entorno:** uv + Python 3.12 (`uv.lock`).
- **Datos:** Parquet (fuente de verdad) y DuckDB 1.5 como motor; el `.duckdb` es derivado.
- **Librerías:** pandas y polars, **svy** para encuestas, pyreadstat (SPSS/Stata), zstandard.
- **Metadatos:** Frictionless Data Package v2 con términos DCAT/PROV.
- **Tareas:** justfile.
- **Fundamentos:** `docs/especificaciones/stack.md`.
- **Futuro (fase 5):** FastAPI con DuckDB en solo lectura sobre el cubo, desplegado en la nube con Docker.

## 7. Gobierno del proyecto

- **Decisiones del dueño:** fechadas en `docs/decisiones.md`. Varias del 10/10 están aprobadas «con cargo a revisión después del piloto».
- **Cambios importantes:** implementador → analista o auditor independiente → verificación → fusión a `main` con `--no-ff`. Las ramas se borran una vez fusionadas; los hitos llevan etiqueta (`antes-de-lima`, `piloto-aceptado`, `piloto-cerrado`).
- **Estado y siguientes pasos:** `docs/estado.md` y `docs/hoja_de_ruta.md`.

## 8. Límites actuales

- **Sin web ni LLM:** la pregunta debe llegar estructurada (opciones de la CLI o consulta mínima en JSON). Lo siguiente es el intérprete LLM (slice 2, fase 5b) y la API y web (fase 5c).
- **Solo los 9 indicadores del piloto;** la Ola 1 espera GA-13 (gasto en proyectos fuera del detalle de inversiones).
- **Series incompletas:**
  - el criterio vigente de anemia solo tiene 2024–2025 (el recálculo de años anteriores está decidido para después del MVP);
  - el SIEN solo tiene 2025. Está validado contra el INS, pero no es comparable con la ENDES y puede subestimar la anemia (lo dice el propio INS).
- **Riesgo operativo:** el almacén de crudos (1,2 GB) no tiene respaldo externo; si se pierde, no se puede reconstruir sin volver a descargar.
- **Pendientes del dueño:**
  - las decisiones X-01 a X-08 de `docs/decisiones.md` (entre ellas el texto de «¿Qué puedo hacer?»; X-02, conteo en Q2; X-03, gasto del mismo año en CR-01; X-04, un solo intervalo visible);
  - respaldo del almacén.
- Detalle en `docs/estado.md`.
