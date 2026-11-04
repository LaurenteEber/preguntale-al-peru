# S1-01 — Contrato de la consulta mínima

## Por qué

Es la frontera entre «qué pregunta el usuario» y «cómo se calcula». En el slice 2 el LLM producirá exactamente este objeto y nada más (P-01). Debe ser pequeño, cerrado y validable.

## Contexto

- Hoy la consulta (`tests/fixtures/consultas_piloto/q*.yaml`) mezcla lo pedido con el plan de cálculo (lista de cifras, plantilla). Ver `docs/especificaciones/motor.md` §4.
- Vocabulario de intenciones ya existente: `respuesta.VOCAB_INTENCION` = `nivel_actual`, `evolucion`, `comparacion`, `cruce`, `identificar_extremo`, `efecto`.

## Tareas

1. Esquema JSON en `curados/motor/esquemas/consulta_minima.schema.json` (JSON Schema 2020-12). Campos:
   - `intencion` (vocabulario de arriba).
   - `tema` (vocabulario cerrado = valores de `dim_indicador.tema`: `anemia`, `desnutricion_cronica`, `pobreza_monetaria`, `gasto_publico`; ver `parametros_motor.yaml` → `temas`) **o** `indicador` (un `dim_indicador.id`). Uno de los dos, obligatorio. En gasto, el tema concreto (`cpt_…`, `fun_…`) nunca lo pone la consulta: lo fija la clave de `map_intencion_tema` (R-GASTO-08b) indicada en `temas.gasto_publico_clave_map`. Las demás claves de gasto de esa tabla dan `no_se_puede` «tema fuera del piloto» (el cubo solo tiene los grupos ex-PAN).
   - Un cruce o un efecto (Q3: gasto y anemia) lleva un solo `tema`, el de la pregunta (`gasto_publico` o `anemia`); el otro lado lo pone el planificador desde `cruces_permitidos.yaml` (S1-03).
   - `territorio`: `{texto}` (lo que escribió la persona) **o** `{ubigeo}` **o** `{ambito}` (`LIMA_METROPOLITANA`, `LIMA_REGION`, `CALLAO`…) **o** `{nacional: true}`. Para `identificar_extremo`: `{nivel, dentro_de?}` (p. ej. distrito dentro del Perú).
   - `periodo`: `{tipo: ultimo}` | `{tipo: anio, anio}` | `{tipo: serie, desde?, hasta?}`.
   - `comparar_con` (opcional): otro territorio con la misma forma (para `comparacion`).
   - `pregunta_original` (opcional, texto) y `idioma` (por defecto `es`).
2. Módulo `pap/motor/consulta.py`: carga y valida contra el esquema y devuelve errores en lenguaje sencillo (p. ej. «Falta el lugar: ¿de qué departamento, provincia o distrito?»).
3. Equivalencias para Q1–Q4 en `curados/motor/consultas_minimas/q1.json … q4.json`, escritas desde la pregunta original de cada `q*.yaml`. El texto del territorio debe identificar un solo lugar, para que la regresión no caiga en una aclaración: Q1 `{"texto": "departamento de Huancavelica"}` (Huancavelica es también provincia y distrito); Q2 `{"texto": "Ayaviri, Melgar"}` (existe otro Ayaviri, 151004, en Yauyos); Q3 `{"texto": "San Juan de Lurigancho"}`; Q4 `identificar_extremo` con `{nivel: distrito}`. Los mensajes de error van en `curados/motor/textos/errores_consulta.yaml`.
4. Pruebas: los cuatro casos válidos y al menos 10 inválidos (intención fuera del vocabulario, tema e indicador a la vez, periodo imposible, territorio vacío, `comparar_con` sin intención de comparación…).

## Criterios de aceptación

- [ ] El esquema rechaza todo campo no declarado (`additionalProperties: false`).
- [ ] Q1–Q4 tienen su consulta mínima y validan.
- [ ] Cada error de validación tiene un mensaje para el usuario sin jerga ni nombres de campos.
- [ ] La consulta mínima no contiene cifras, años de comparación elegidos por el usuario más allá de `periodo`, ni nombres de plantillas.

## Fuera

Interpretar texto libre (slice 2). Resolver el territorio (S1-02).
