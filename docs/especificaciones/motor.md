# Especificación del validador y el motor del piloto

Versión 1.0 · 10 de octubre de 2026 · Sprint P0 · Estado: **aprobada por el dueño** (10/10/2026, con cargo a revisión después del piloto).

Este documento fija los contratos entre las piezas del piloto. Las reglas no se repiten aquí: viven en `reglas/reglas.json`. Las decisiones están en `docs/decisiones.md`.

## 1. Alcance

- **Preguntas:** las 1 a 4 de la prueba de reglas (`04_reglas/prueba/resultado_prueba.json`):
  - Q1: anemia en Huancavelica (ENDES);
  - Q2: anemia en los establecimientos de Ayaviri (SIEN);
  - Q3: gasto de San Juan de Lurigancho junto a la anemia (gasto MEF y CR-01);
  - Q4: distrito más pobre (Mapa de Pobreza 2018 y ENAHO).
- **Sin LLM** (decisión del 10/10/2026). Cada pregunta entra como una **consulta estructurada** (§4). El texto sale de plantillas.
- **Indicadores:** los 9 de `dim_indicador`. **Cruces:** solo CR-01, que ya tiene el visto del dueño.
- **Se acepta cuando** Q1–Q4 producen cifras, semáforo, ficha y texto correctos. Se comparan con `resultado_prueba.json`, ajustado a las decisiones posteriores a la prueba (gasto rondas 1–2, Lima L1–L9 y P0). El juez es un auditor independiente (P4).
- **Fuera:**
  - la web y el LLM (fase 5);
  - la Ola 1, GA-13 y el verificador R;
  - la validación de los 3 avisos del corrector por terceros (siguen como aviso);
  - la evolución del SIEN en Q3: respuesta parcial con piso ámbar (R-CRUCES-10).

## 2. Arquitectura

```
biblioteca (capa 0 + estandarizada + tablas curadas)
   │  P1  pap calcular                → biblioteca/indicadores/fact_indicador.parquet (cubo) + manifiesto
   ▼
consulta.yaml ──P3 motor──► plan (cifras pedidas) ──► filas del cubo ──P2 validador (etapas 0–10)──► cifras con estado,
                                ▲                                         │ acciones y registro
                                └──── R-MOTOR-01: degradar (otro nivel o años) ◄──┘
   ──► semáforo de cifra (R-CRUCES-09) ──► cruces (CR-01) ──► semáforo de respuesta (R-CRUCES-10)
   ──► ficha corta y larga (R-LENGUAJE-01, plantilla) ──► texto (plantilla + corrector R-LENGUAJE-02/03) ──► respuesta.json + .md
```

Principios, todos ya decididos antes:
- Ningún número sale del texto: el texto solo rellena marcadores `{{c:id_cifra}}` con valores del cubo.
- El cálculo es determinista y reproducible bit a bit.
- Un metadato faltante nunca deja pasar una cifra (R-MOTOR-02).
- El gasto se lee solo por las vistas y `gasto_tema()`, y cada consulta pasa por `guardia_gasto.verificar_consulta()`.

## 3. Contrato del cubo: `fact_indicador` (P1)

Una fila por cifra calculable: indicador × año × nivel × territorio × medida × línea. Clave: `indicador_id, anio, nivel, territorio_id, medida, linea`. Se escribe con `salida.guardar` (Parquet zstd ordenado por clave, manifiesto `manifiesto_p1_indicadores.json`, pruebas y revisión).

| Columna | Tipo | Contenido |
|---|---|---|
| `indicador_id` | texto | `dim_indicador.indicador_id` |
| `anio` | entero | año de referencia (Mapa: 2018) |
| `nivel` | texto | valor de `NIVEL_RANK`: `nacional`, `dominio_subnacional`, `departamento`, `provincia`, `distrito`, `establecimiento`, `LIMA_METROPOLITANA`, `LIMA_REGION`, `CALLAO`, `AREA_METROPOLITANA_LIMA_CALLAO` |
| `territorio_id` | texto | `PE`; `urbano`/`rural`; departamento con 2 dígitos; provincia y distrito con el ubigeo INEI de 6 dígitos (la provincia termina en 00); `cod_ipress`; o el `ambito_id` |
| `territorio_nombre` | texto | nombre mostrado (`dim_ubigeo_historico`, rótulos de R-ENC-07 para los ámbitos) |
| `medida` | texto | `proporcion` (encuestas y SIEN), `cobertura` (SIEN), `devengado`, `pim`, `pia` (gasto), `intervalo` (Mapa) |
| `linea` | texto | `cifra`; en el gasto del 15 y el 07 también `referencia_nacional`, `sede_nacional`, `no_asignable_dpto_lima`, `no_asignable_lima_callao` (no se suman a la cifra) |
| `criterio` | texto | `criterio_medicion` del indicador |
| `valor` | doble | proporción en % (1 decimal se aplica al mostrar), monto en soles corrientes; nulo en el Mapa |
| `ee`, `cv` | doble | error estándar (en %) y CV (%) del diseño; nulos donde no aplica |
| `ic_inf`, `ic_sup` | doble | IC 95 %: Korn-Graubard NCHS (encuestas), Wilson (SIEN), publicado (Mapa) |
| `metodo_ic` | texto | `korn-graubard` · `wilson` · `publicado_inei` · nulo |
| `gl` | entero | grados de libertad del diseño (conglomerados − estratos en el dominio) |
| `n_muestra` | entero | casos sin ponderar (encuestas), niños tamizados (SIEN) |
| `n_efectivo`, `deff` | doble | n efectivo = p(1−p)/V; efecto de diseño respecto de un muestreo simple con reemplazo (`wr`: los pesos de la ENDES están normalizados) |
| `numerador`, `denominador` | doble | conteos o montos (SIEN, cobertura); nulos en encuestas |
| `cota_inf`, `cota_sup` | doble | cobertura del SIEN: por procedencia, y por procedencia + establecimiento sin procedencia |
| `grupo_robusto_nacional`, `grupo_robusto_regional` | entero | Mapa de Pobreza 2018 |
| `metodo_territorio` | texto | cómo se asignó el territorio: `ubigeo`, `estrato_hv022`, `variable_dominio`, `departamento_meta`, `ubigeo_eess`, `ubigeo_procedencia` |
| `avisos` | texto (JSON) | avisos que ya conoce el cálculo, p. ej. `ambito_no_dominio`, `ambito_por_estrato`, `estrato_un_conglomerado`, `sin_casos` |
| `estado_calculo` | texto | `calculada` · `sin_casos` · `no_calculable` (con `motivo_calculo`) |
| `validada_dorada` | texto | `id_cifra` de la dorada bloqueante que la valida (R-ENC-18) o nulo |
| `version_tabla` | texto | versión del constructor |

El cubo **no decide** si una cifra se publica: eso es del validador (P2). El cubo calcula todos los niveles válidos de `dim_indicador` (también los que el validador suprimirá) para que la degradación (R-MOTOR-01) solo lea filas.

Insumos y estimadores:
- **ENDES y ENAHO:** svy 0.32.1, Taylor, `singleton = center` (= R `lonely.psu = "adjust"`). La estimación es por subpoblación (`where`), con todos los conglomerados del año.
- **SIEN:** suma de numeradores y denominadores; IC de Wilson.
- **Gasto:** `gasto_tema('<tema_id>')` y `ambito_gasto`.
- **Mapa:** intervalo y grupos publicados, sin cifra puntual.

## 4. Contrato de la consulta (P3)

`tests/fixtures/consultas_piloto/qN.yaml`, versionado en git.

```yaml
id: Q1
pregunta: "<texto de la pregunta 1 de la prueba de reglas>"   # ejemplo ilustrativo
intencion: evolucion            # nivel_actual | evolucion | comparacion | cruce | identificar_extremo
territorio: {nivel: departamento, id: "09", nombre_pedido: Huancavelica}
periodo: {tipo: serie, desde: 2015, hasta: ultimo}     # o {tipo: anio, anio: 2025} | {tipo: ultimo}
cifras:
  - {id: anemia_hvca_2025, indicador: endes_anemia_6_35m_oms2024, rol: principal, anio: ultimo}
  - {id: anemia_hvca_serie, indicador: endes_anemia_6_35m, rol: principal, anios: [2015, 2024], comparar: true}
cruce: null                     # Q3: CR-01
plantilla: q1_evolucion         # curados/motor/plantillas/
```

- La consulta solo dice **qué** se pide. Nivel, años y suplentes los resuelve el motor con las reglas: R-MOTOR-03 para el periodo; R-TERRITORIO-09 para los homónimos («Huancavelica» es departamento, provincia y distrito); L4 para «Lima», que pregunta y sin respuesta toma LM.
- Las 4 consultas del piloto se escriben en P3 a partir de `resultado_prueba.json`.

## 5. Contrato del validador (P2)

**Entrada por cifra (`CifraEnEvaluacion`):**
- la fila del cubo y los metadatos de `dim_indicador`;
- la consulta: nivel y años pedidos, rol;
- el contexto de la biblioteca: catálogo (R-DEP-01), `dim_dominio`, `inferencia_verificada.csv`, manifiestos, `cifras_doradas` y `cruces_permitidos`.

**Reglas:**
- Cada regla del alcance es una función pura `evaluar(cifra, ctx) -> Resultado | None`, registrada con su id.
- Alcance: las reglas de `reglas/alcance_piloto.csv` con `necesaria_piloto ∈ {si, solo_infraestructura}`.
- `Resultado` = `accion` (vocabulario de R-MOTOR-02) + `motivo` + `mensaje_id` (texto fijo de `reglas.json`) + parámetros usados.
- Una prueba exige que el registro coincida con el alcance: ni faltan reglas ni sobran.

**Orden:** etapas 0 a 10 de `reglas.json`. Dentro de una etapa, en el orden de la etapa. Dentro de una regla gana la primera cláusula que se cumple.

**Precedencia (R-MOTOR-02):**
- Entre reglas gana la acción más restrictiva de `orden_restriccion`.
- `rotular`, `advertir` y `revision_humana` se acumulan.
- Un campo requerido nulo → `suprimida` por `metadato_faltante`.

**Degradación (R-MOTOR-01):**
- Ante `agregar_nivel` o `agrupar_anios`, el motor pide al cubo la fila siguiente de la secuencia de su naturaleza y la vuelve a evaluar desde la etapa 1.
- Cada paso queda en el registro. Si la secuencia se agota → `sin_datos`.

**Salida por cifra:**
- `estado_cifra` (vocabulario de R-MOTOR-02);
- `accion_final`, rótulos, avisos y mensajes;
- `semaforo_cifra` (R-CRUCES-09, etapa 7) con `motivos_semaforo`;
- `registro`: la lista de (regla, cláusula, acción) y los pasos de degradación.

**Pruebas (P2):**
- Por regla, al menos un caso que la dispara y uno que no. Los casos los escribe un analista independiente a partir de `reglas.json`, no del código.
- Un auditor independiente compara la implementación con el texto vigente de cada regla.

## 6. Contrato de la respuesta (P3)

`respuesta.json`:
- `consulta`, `version_biblioteca` (huella del manifiesto del cubo y commit);
- `cifras[]` (salida del validador más el valor formateado), `cruces[]` y `semaforo_respuesta` (R-CRUCES-10);
- `ficha` con `corta` (≤ 4 líneas, R-LENGUAJE-01) y `larga` (secciones de `reglas.json → ficha_limites`);
- `texto` (plantilla rellenada), `corrector` (resultado de R-LENGUAJE-02/03 y avisos) y `registro`.

`respuesta.md` es la vista legible. La ficha la genera la plantilla con la salida del validador; nunca se redacta a mano.

## 7. Código y comandos

| Pieza | Dónde | Comando |
|---|---|---|
| Cálculo (P1) | `src/pap/motor/calculo.py`, `motor/biblioteca.py` (conexión de solo lectura con vistas del gasto y guardia) | `pap calcular` |
| Validador (P2) | `src/pap/motor/validador/` (registro, etapas, precedencia, degradación) | `pap validar-reglas` (pruebas de casos) |
| Respuesta (P3) | `motor/consulta.py`, `motor/semaforo.py`, `motor/ficha.py`, `motor/texto.py`; consultas y plantillas en `curados/motor/` | `pap preguntar tests/fixtures/consultas_piloto/q1.yaml` |
| Aceptación (P4) | `03_auditoria/piloto_aceptacion/` | — |

Dependencias nuevas (P1): `svy==0.32.1` y `polars` en `pyproject.toml` / `uv.lock`. En el Mac: `uv sync`.

## 8. Sprints

| Sprint | Rama | Se acepta cuando |
|---|---|---|
| P0 | `piloto-p0` | Reglas regeneradas sin pruebas de consistencia fallidas; `pap construir indicadores` sin bloqueantes; decisiones registradas; esta especificación |
| P1 | `piloto-p1` | `fact_indicador` cubre los 9 indicadores en todos sus niveles válidos. Reproduce el **100 % de las cifras doradas bloqueantes de encuestas** (cifra a ± 0,1 pp, casos exactos y CV ± 0,1 donde el INEI los publica) y los **controles del gasto** (ex-PAN y opción C, 2023–2025). El Mapa coincide con lo publicado. Reproducible bit a bit (dos construcciones, misma huella) |
| P2 | `piloto-p2` | Las reglas del alcance implementadas, con casos que disparan y que no; auditoría independiente «apto» |
| P3 | `piloto-p3` | Q1–Q4 producen `respuesta.json` y `.md` completas |
| P4 | — | Auditor independiente: «apto»; se cierra la fase 4 |
