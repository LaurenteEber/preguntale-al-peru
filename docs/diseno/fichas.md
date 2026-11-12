# Fichas de tabla y bloques temáticos

Documento de diseño · Pregúntale al Perú · 12 de noviembre de 2026 · Ubicación: `docs/diseno/fichas.md`

Complementa a `docs/diseno/motor_inferencia.md` (§7, índice y tablas curadas). Aprobado por el dueño el 12/11/2026: ficha por tabla, nivel de bloque, población estructurada, campos válidos para cualquier fuente y temas provisionales.

## 1. Para qué

**En sencillo.** Hoy el motor sabe qué variables tiene cada tabla, pero no tiene un resumen de qué es cada tabla ni de qué asuntos trata. Las fichas dan ese resumen en tres niveles. Sirven para dos cosas:
- que una persona (o el agente) entienda rápido qué hay en cada fuente;
- que el motor busque en dos pasos: primero el asunto, después la pregunta exacta. Es la base para responder con varias encuestas a la vez (niveles 1 y 2).

| Nivel | Qué describe | Cuántos (ENDES 2024) | Quién lo escribe |
|---|---|---|---|
| **Descarga** | Qué se baja del INEI y con qué códigos | 13 módulos y 10 documentos | agente, desde el catálogo |
| **Ficha de tabla** | Qué es cada tabla: a quién describe, cómo se une, si se puede estimar | 34 | 10 campos a mano; el resto se arma solo |
| **Bloque** | Un grupo de preguntas del mismo asunto dentro de una tabla | unos 150 a 250 (se mide en M1) | agente propone; auditor y dueño revisan |

La **ficha común** (concepto o indicador, que une fuentes distintas) se define en el anexo de varias fuentes, no aquí. Los bloques son su insumo.

## 2. Reglas

1. **Una sola fuente de verdad por dato.** Lo que ya está en una tabla curada o en el índice no se vuelve a escribir: la ficha lo toma de ahí.
2. **Lo escrito a mano se escribe una vez por tabla,** con su rango de años, no una vez por año.
3. **El tema se escribe en el bloque.** La tabla lo hereda como lista y la variable lo hereda de su bloque.
4. **Los temas son provisionales** (`tema_estado: provisional`) hasta que el dueño apruebe la taxonomía. Cambiar la taxonomía es editar `temas.yaml` y reasignar; no cambia ninguna cifra.
5. **Nada de esto cambia cifras.** El cubo `010ea965` y las recetas no se tocan.

## 3. Archivos

| Archivo | Contenido | Origen |
|---|---|---|
| `curados/inferencia/descargas/<encuesta>_<anio>.yaml` | Lista de descargas (ya existe; se amplía, §4) | a mano, desde el catálogo |
| `curados/inferencia/temas.yaml` | Vocabulario de temas y subtemas, con su estado (§8) | a mano |
| `curados/inferencia/fichas/<encuesta>.yaml` | Los campos a mano de cada tabla (§5) | a mano |
| `curados/inferencia/bloques/<encuesta>.yaml` | Los bloques de cada tabla (§6) | a mano (propuesto por el agente) |
| `biblioteca/variables/fichas_tabla.parquet` | Ficha completa por encuesta × año × tabla | generado |
| `biblioteca/variables/bloques.parquet` | Bloques por encuesta × año, con sus variables resueltas | generado |
| `biblioteca/variables/variables.parquet` | Gana la columna `bloque_id` | generado |

Comandos (módulo `src/pap/inferencia/fichas.py`):
- `pap fichas generar --encuesta ENDES --anio 2024`: arma los Parquet.
- `pap fichas validar`: aplica las reglas del §9; sale con 1 si alguna falla.
- `pap fichas ver <tabla> [--anio]`: muestra la ficha en texto, para personas.

## 4. Descarga: campos que se agregan

Al YAML que ya existe:

```yaml
encuesta: {anio: 2024, codigo: 968, periodo_codigo: 5, periodo_nombre: "Unico"}
modulos:
  - codigo: 1638
    nombre: "Peso y talla - Anemia"
    formato: STATA
    url: https://…/STATA/968-Modulo1638.zip
    recurso: endes-2024-anemia
    tablas: [RECH5, RECH6, REC44]        # nuevo: se comprueba contra el ZIP
documentos:
  - codigo_documento: 7                  # nuevo: el número del listado del INEI
    nombre: "Ficha Técnica"
    url: https://…
    recurso: endes-2024-ficha-tecnica
```

- Documentos que se agregan a la ENDES 2024 (decisión del dueño, 12/11/2026): n.º 8 «Manual de la Entrevistadora», n.º 9 «Manual del Antropometrista» y n.º 11 «Identificadores de las bases de datos». El n.º 10 no se baja.
- Al registrar, `pap registrar --url-descarga` guarda la URL exacta de cada archivo (`download_url`; la página general del portal es `access_url`).
- Las copias de la ficha y de los cuestionarios que vienen dentro de los ZIP no se tocan.

## 5. Ficha de tabla

Una ficha por encuesta × año × tabla. Ejemplo: RECH6 de la ENDES 2024.

### 5.1 Campos a mano (`curados/inferencia/fichas/ENDES.yaml`)

```yaml
version: 0.1.0
encuesta: ENDES
tipo_fuente: muestra                     # muestra | registro | censo | presupuesto
tablas:
  RECH6:
    anios: [2024, 2024]
    nombre_corto: "Peso, talla y hemoglobina de niñas y niños"
    descripcion: "Mediciones de peso, talla y hemoglobina de los menores de 6 años del hogar."
    cuestionario: hogar                  # hogar | individual | salud (vocabulario por encuesta)
    secciones: ["Antropometría y hemoglobina"]
    tipo_tabla: medicion                 # base | detalle | medicion | lista | calendario | construida
    poblacion:
      texto: "niñas y niños menores de 6 años"
      sujeto: nino                       # vocabulario de sujetos del índice (§7.2 del motor)
      edad_min: 0
      edad_max: 71
      edad_unidad: meses                 # meses | anios
      sexo: ambos                        # ambos | mujer | hombre
      condicion: "listados en el hogar"
    quien_tiene_fila: "todos los menores de 6 años listados, con o sin medición"
    informante: "personal de campo"
    modo: medido                         # declarado | medido | mixto
    avisos: []
    documentos:
      - {recurso: endes-2024-anemia, miembro: "Diccionario - RECH6.pdf"}
      - {recurso: endes-2024-cuestionario-hogar, paginas: "…"}
    estado: propuesto                    # propuesto | revisado
```

- Los valores del ejemplo son ilustrativos: cada campo se llena leyendo el diccionario y el cuestionario.
- `poblacion` estructurada sirve al nivel 2: dos fuentes solo se emparejan si su población es compatible. Un campo que no aplica va vacío, nunca inventado.
- `avisos` recoge límites conocidos de la tabla, con su consulta (por ejemplo, en REC93DVdisciplina: C-M0-05-2).
- Para fuentes que no son muestras (más adelante), `cuestionario`, `informante` y `modo` pueden ir vacíos y se agrega `cobertura` en palabras («atenciones en establecimientos del MINSA»).

### 5.2 Campos derivados (los arma `pap fichas generar`)

| Campo | De dónde sale |
|---|---|
| `modulo_codigo`, `modulo_nombre`, `codigo_encuesta`, `periodo` | `descargas/<encuesta>_<anio>.yaml` (por `tablas`) |
| `recurso`, `formato`, `huella_datos`, `n_filas`, `n_variables` | `archivos.parquet` y el manifiesto |
| `unidad`, `llave`, `uniones`, `tabla_base` | `archivos_<encuesta>_<anio>.yaml` |
| `variables_por_clase`, `baterias` (prefijo y número de variables) | `variables.parquet` |
| `tiene_diseno`, `peso`, `estrato`, `upm`, `nivel_submuestra`, `permite_totales` | `diseno_muestral.csv` (`permite_totales` = no si `peso_normalizado`) |
| `alcance_territorial` | `catalogo/inferencia_verificada.csv` y `territorios.yaml` |
| `anios_disponibles`, `cambios_vs_anio_anterior` | `archivos.parquet` y `variables.parquet` de todos los años (desde M2) |
| `n_propuesto`, `n_revisado`, `controles` | `variables.parquet` |
| `temas` (lista, con el principal primero) | los bloques de la tabla; el principal es el del bloque con más variables |
| `bloques` (lista de ids) | `bloques/<encuesta>.yaml` |
| `recetas`, `conceptos` | `recetas/*.yaml` y `concepto_id` del índice |

`tiene_diseno: no` significa que la tabla todavía no se puede estimar: el verificador ya rechaza esos planes. Al cerrar M0, en la ENDES 2024 solo 6 de las 34 tablas tienen diseño declarado. La clase `categoria` o `medida` de cada variable se llena en M1-05; hasta entonces casi todo el índice la tiene vacía.

## 6. Bloque

**En sencillo.** Una tabla grande mezcla asuntos. REC43 trae vacunas, diarrea, infecciones respiratorias y suplementos de hierro. Un bloque es cada uno de esos grupos. Es la unidad con la que el motor reconoce «de qué trata» una pregunta antes de elegir la variable exacta.

```yaml
# curados/inferencia/bloques/ENDES.yaml
bloques:
  - id: endes_rec43_suplemento_hierro
    tabla: REC43
    anios: [2024, 2024]
    nombre: "Suplementos de hierro y micronutrientes en niñas y niños"
    descripcion: "Si la niña o el niño recibió hierro o micronutrientes y en qué forma."
    variables: {prefijos: [], lista: [], rango: ["<primera>", "<última>"]}   # una de las tres formas
    tema: salud_infantil
    subtema: suplementos
    tema_estado: provisional
    papel: servicio                      # resultado | servicio | recurso | contexto
    poblacion: {}                        # vacío = la de la tabla; se llena solo si es más estrecha
    ventana_referencia: "últimos 7 días" # si es común a todo el bloque
    seccion_cuestionario: "…"
    estado: propuesto
```

Reglas:
- Cada variable de clase `categoria` o `medida` pertenece a **un solo** bloque. Las llaves, pesos, diseño y geografía no llevan bloque.
- Las variables de un bloque se declaran por prefijo, por rango de posición entre dos códigos o por lista. `pap fichas generar` las resuelve y escribe `bloque_id` en el índice.
- Un bloque vive en una sola tabla. El mismo asunto en dos tablas son dos bloques con el mismo tema y subtema; los une la ficha común.
- Punto de partida: las baterías del índice (`grupo`) y las secciones del cuestionario. El agente propone y la revisión es por lote.
- `papel` es el de la ficha común: permite armar la cadena recurso → servicio → resultado cuando entren otras fuentes.

## 7. Uso en la búsqueda

- **Paso 1:** el recuperador busca sobre bloques, conceptos y recetas (cientos de textos: nombre, descripción, tema, subtema y sinónimos).
- **Paso 2:** busca variables solo dentro de los bloques elegidos.
- En M1 (una encuesta, un año) el recuperador sigue el §10 del motor y usa el bloque de dos formas: su texto entra como campo de búsqueda de cada variable y los candidatos se agrupan por bloque. El modo de dos pasos queda detrás del parámetro `recuperador.dos_pasos` (inicial: `false`) y se mide con el conjunto de evaluación: se activa si mejora el recall@20.
- Con varias fuentes, el paso 1 es lo que permite al orquestador pedir «un plan por fuente» sobre el mismo tema.

## 8. Temas provisionales

`curados/inferencia/temas.yaml`, propuesto por el supervisor con las etiquetas de las variables (sin leer aún los diccionarios). Criterio: asuntos de la vida de las personas, no sectores del Estado.

| Tema | Subtemas | Tablas de la ENDES 2024 |
|---|---|---|
| `hogar_vivienda` | composición del hogar; vivienda, agua y saneamiento; bienes y riqueza | RECH0, RECH1, RECH23 |
| `educacion` | nivel educativo y asistencia | RECH1, REC0111 |
| `salud_infantil` | anemia y desnutrición; vacunas; enfermedades y suplementos; desarrollo infantil temprano; salud bucal y ocular | RECH6, REC44, REC43, REC95, DIT, CSALUD08 |
| `salud_materna_reproductiva` | embarazo, control prenatal y parto; lactancia y posparto; fecundidad y nacimientos; planificación familiar | REC41, REC94, REC42, RE223132, REC21, REC82 |
| `salud_adultos` | enfermedades crónicas; tabaco y alcohol; salud mental; prevención del cáncer; peso y anemia en mujeres; VIH e infecciones de transmisión sexual | CSALUD01, RECH5, RE758081 (por confirmar) |
| `acceso_salud` | seguro de salud | RECH4, REC91 (por confirmar) |
| `familia_pareja` | unión y convivencia; trabajo de la mujer y de la pareja | RE516171, RE758081 (por confirmar) |
| `violencia` | violencia contra la mujer; castigo y disciplina infantil | REC84DV, REC93DVdisciplina |
| `mortalidad` | mortalidad infantil; mortalidad materna; muertes en el hogar | REC21, REC83, RECHM |
| `programas_sociales` | un subtema por programa | las 8 tablas PS |
| `identidad_cultura` | lengua materna y autoidentificación étnica | REC91 (por confirmar) |

RECH0 y REC0111 son tablas base (`tipo_tabla: base`): sirven a todos los temas.

Esquema de `temas.yaml`: `id`, `nombre`, `subtemas: [{id, nombre}]`, `estado: provisional | aprobado`, `version`.

## 9. Validación (`pap fichas validar`)

1. Toda tabla del índice tiene ficha, y toda ficha corresponde a una tabla que existe en sus años.
2. Las tablas de cada módulo en `descargas` son exactamente los miembros de datos de su ZIP.
3. Los vocabularios se respetan (`tipo_tabla`, `modo`, `papel`, `sujeto`, `edad_unidad`, `sexo`, temas y subtemas de `temas.yaml`).
4. Ninguna variable `categoria` o `medida` queda sin bloque o en dos bloques. Se informa la cobertura; el umbral exigible es 100 % en las tablas pasadas a `revisado`.
5. La población de un bloque no es más amplia que la de su tabla.
6. `edad_min ≤ edad_max`; si la tabla trae la variable de edad, el rango observado cae dentro del declarado (se informa la diferencia).
7. Cada documento citado existe como recurso registrado y, si nombra un miembro, ese miembro está en el ZIP.
8. Lo generado es reproducible: dos corridas dan los mismos Parquet.

## 10. Estados y revisión

- El agente escribe fichas y bloques en `propuesto`.
- El auditor-agente los revisa contra el diccionario de cada tabla y el cuestionario; el dueño da el visto por lote y pasan a `revisado` (mismo flujo que el índice, §26.4 del motor).
- `tema_estado` es independiente: una ficha puede estar `revisado` con temas `provisional`.
- Solo los bloques `revisado` se usan en respuestas públicas.

## 11. Dónde entra en el backlog

| Historia | Qué |
|---|---|
| M1-00 | Ampliar `descargas/endes_2024.yaml` (§4); bajar y registrar los documentos n.º 8, 9 y 11 |
| M1-06 | `temas.yaml`, fichas de las 34 tablas, bloques de las tablas de niño, mujer y hogar; `pap fichas generar`, `validar` y `ver`; revisión y visto por lote |
| M1-09 | El recuperador usa el texto del bloque y agrupa por bloque; se mide `recuperador.dos_pasos` |
| M2 y M3 | Fichas y bloques de los demás años y de la ENAHO; `cambios_vs_anio_anterior` |
| Anexo de varias fuentes | Ficha común, enlace entre bloques de fuentes distintas, orquestador |

## 12. Decisiones registradas (12/11/2026, dueño)

- La ficha es por tabla, no por módulo; el módulo es un campo.
- Se agrega el nivel de bloque; el tema y el subtema se escriben ahí.
- Población estructurada y campos válidos para cualquier fuente (`tipo_fuente`, `cobertura`).
- Temas y subtemas provisionales propuestos por el supervisor; se ajustan con la taxonomía definitiva.
- K-01 revisada: la lista de descargas es correcta; se amplía según el §4.

Se registran en `docs/decisiones.md` como ampliación de F-01 y F-05 (no llevan fila nueva).
