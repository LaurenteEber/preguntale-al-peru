# Contrato del validador (P2)

10/10/2026. Complementa `especificacion_validador_motor.md` §5. Lo usan los implementadores de las reglas y el analista que escribe los casos de prueba. **La fuente de verdad de cada regla es `reglas/reglas.json`**: condición, parámetros, implementación, mensajes y casos borde. Aquí solo se fijan los nombres de los campos y la forma de los casos.

## 1. Alcance

Las **68 reglas** (67 del análisis del 8/10 + R-ENC-08, que entró por la auditoría de P2) de `reglas/alcance_piloto.csv` con `necesaria_piloto ∈ {si, solo_infraestructura}`, en las etapas de `reglas.json → etapas`.

| Grupo | Etapas | Ámbito | Módulo |
|---|---|---|---|
| A | 0 prerrequisitos; 1 territorio; 2 nivel; 3 denominador | cifra | `reglas_etapa0.py` (incluye `siguiente_paso` de R-MOTOR-01), `reglas_etapa1_3.py` |
| B | 4 precisión; 6 divulgación; 7 semáforo de cifra | cifra | `reglas_etapa4.py`, `reglas_etapa6_7.py` |
| C | 5 series; 8 cruces; 9 semáforo de respuesta; 10 comunicación | 5: cifra · 8–10: respuesta | `reglas_etapa5.py`, `reglas_etapa8_10.py` |

## 2. La cifra (`Cifra`, ámbito «cifra»)

Acceso por atributo: `c.campo` devuelve `None` si falta. `c.req("campo")` lanza `CampoFaltante`, y el núcleo lo convierte en `suprimir` por `metadato_faltante` (R-MOTOR-02). Una regla usa `req` para todo campo **requerido** cuyo vacío no tenga un caso definido en el texto de la regla.

**a) Fila del cubo** (`fact_indicador`, especificación §3):
- `indicador_id, anio, nivel, territorio_id, territorio_nombre, medida, linea, criterio`;
- `valor` (en % para proporciones y coberturas; en soles para el gasto), `ee` (en %), `cv` (en %), `ic_inf`, `ic_sup` (en %), `metodo_ic`;
- `gl, n_muestra, n_efectivo, deff, numerador, denominador, cota_inf, cota_sup`;
- `grupo_robusto_nacional, grupo_robusto_regional, metodo_territorio`;
- `avisos` (lista), `estado_calculo, motivo_calculo, validada_dorada, indicador_validado`.

**b) Metadatos del indicador**, al primer nivel, con los mismos nombres que en `curados/capa0/dim_indicador.yaml`. Los principales:
- `naturaleza_dato, tipo_medida, base_geografica_usada, fuente_principal, tipo_estimacion, origen_cifra, criterio_medicion`;
- `concepto_medido, rank_concepto, tema, universo, poblacion_objetivo`;
- `es_socioeconomico, velocidad_cambio, sensibilidad_divulgacion, subregistro_conocido, insumos` (lista de `{id, rol}`);
- `requiere_denominador, tipo_denominador, denominador_principal, requiere_estandarizacion, n_desagregaciones_adicionales, tasa_suavizada, periodicidad_estimacion`;
- `nivel_territorial_inferencia, niveles_validos, anios_disponibles, variables_diseno, dominios_inferencia, tipo_aplicacion, metodo_ic, validado_contra_oficial, quiebres, rotulo_medida, tema_id, unidad_observacion`.

**c) Alias que crea el núcleo:**
- `n_sin_ponderar = n_muestra`; `base_geografica = base_geografica_usada`; `fuente = fuente_principal`.
- En proporciones (no coberturas): `p` y `estimacion` en proporción (0–1) y `ee_prop` = ee/100. En el resto, `estimacion = valor`.

**d) Consulta** (lo pide el motor en P3):
- `nivel_pedido`, `territorio_pedido` (texto), `anio_pedido`;
- `rol` (`principal` | `contexto`), `es_principal` (bool), `intencion_pregunta` (`nivel_actual` | `evolucion` | `comparacion` | `cruce` | `identificar_extremo`), `id_cifra`.

**e) Series** (etapa 5 y ENC-11):
- `serie`: lista de filas del cubo del mismo indicador, nivel y territorio, para los años pedidos;
- `comparacion`: la fila del año con que se compara, con `prueba_cambio` = `{diferencia, ee_diferencia, p_valor, significativa}` cuando el motor la calcula.

**f) Estado** que actualiza el validador:
- `estado_cifra`, `accion_final`, `nivel_publicado`, `motivo_nivel` (lista de pasos), `periodo_agrupado` (`[desde, hasta]`), `cifra_original`;
- `resultados_previos` (los `Resultado` de las reglas ya corridas en esta cifra) y `accion_previa`.

**f2) Campos del cubo v1.1.0** (agregados en P2): `poblacion` (total del territorio, proyección distrital oficial; el establecimiento lleva la de su distrito); `ubigeo_inei`; `fecha_corte` (corte declarado; nulo si la fuente no lo declara) y `fecha_descarga`; `anio_cerrado`; `pct_gasto_atribuible` (fracción 0–1, R-GASTO-03).

**g) Gasto, de la fila y su consulta:**
- `pct_gasto_atribuible`;
- en la línea de la cifra: `linea, avisos` (`sesgo_sede`, `linea_referencia_nacional`, `ejecutoras_mixtas`, `callao_canasta_no_comparable`);
- `fase_gasto` (`devengado` | `pim` | `pia` = `medida`), `precios` (`corrientes`), `anio_cerrado` (bool), `fecha_corte`;
- `bloque_consolidado` (siempre `gasto_final` en `gasto_tema`), `tema_id, cadena`, `pim, pia, devengado` (si el motor los junta en una cifra).

## 3. La respuesta (`Respuesta`, ámbito «respuesta», etapas 8–10)

- `intencion_pregunta, nivel_pedido, territorio_pedido`;
- `cifras`: lista de `Cifra` ya evaluadas, con `id_cifra`, `rol`, `es_principal`, `estado_cifra`, `semaforo_cifra`, `motivos_semaforo`;
- `cruces`: lista de `{id_cruce, a, b, presentacion, nivel, anios}`, donde `a` y `b` son `id_cifra`;
- `respuesta_parcial` (bool), `nivel_respuesta`;
- `texto` (borrador con marcadores `{{c:id_cifra}}`), `ficha` (`{corta, larga}`), `cifras_permitidas`.

## 4. Resultado de una regla

`Resultado(regla, accion, motivo, clausula=None, detalle={}, mensaje=None, rotulo=None, aviso=None, nivel_minimo=None, modo=None, objetivo=None, modificador=False)`.

- **Cifra que no puede publicarse → `bloquear`** (el núcleo lo normaliza a `suprimir`). `bloquear_cruce` es solo para cruces, series y comparaciones: en una cifra, por sí solo, la deja publicable.
- `accion`: vocabulario de R-MOTOR-02. Las salidas de `normalizacion_salidas` (`bloquear`, `publicar_rango`, `nota`, `preguntar`, `no_comparar`…) se aceptan y el núcleo las normaliza.
- `motivo`: código corto. Usar los de las reglas: `precision`, `pocos_casos`, `nivel_no_representativo`, `base_establecimiento`, `cobertura_mayor_110`, `divulgacion`, `divulgacion_nivel`, `sin_datos`, `insumo_en_ingesta`, `metadato_faltante`, `criterio_distinto`, `quiebre`, …).
- La regla devuelve `None` si no dispara.
- Por omisión una cifra se **publica**. Una regla que en su cláusula «publicar» no impone nada devuelve `None`, o un `rotular` si agrega un rótulo.
- En reglas de respuesta, `objetivo` = `id_cifra`, `cruce:<id>` o `respuesta`.

## 5. Contexto (`ctx`)

- `ctx.regla(id)`, `ctx.param(id, clave)`; `ctx.pg` (`parametros_globales`: `NIVEL_RANK`, `VOCABULARIOS_INDICADOR`, `anios_choque`…); `ctx.nivel_rank(nivel)`.
- `ctx.catalogo[id_fuente]` (fila de `catalogo/catalogo_fuentes.json`: `compuerta_ingesta`, …); `ctx.inferencia` (filas de `inferencia_verificada.csv`); `ctx.dominios` (reglas de `dominios.yaml`); `ctx.ubigeos` (DataFrame de `dim_ubigeo_historico`).
- `ctx.manifiestos[sprint]`, `ctx.doradas` (filas de `cifras_doradas.csv`), `ctx.cruces` (de `cruces_permitidos.yaml`), `ctx.indicadores[id]`.
- `ctx.fila_cubo(indicador, anio, nivel, territorio, medida=None, linea="cifra")`.
- `ctx.anio_actual = 2026`, `ctx.fecha_referencia = "2026-10-10"`; `ctx.lenguaje` (`reglas.json → lenguaje`), `ctx.ficha` (`ficha_limites`).

## 6. Casos de prueba (`tests/casos_validador/casos/<grupo>.yaml`)

```yaml
- id: R-ENC-03-a                 # único
  regla: R-ENC-03
  descripcion: CV 20 % con n = 300 → referencial
  base: {indicador: endes_anemia_6_35m, anio: 2024, nivel: departamento, territorio: "09"}   # opcional: fila del cubo + metadatos
  cifra: {cv: 20.0, ee: 6.0, valor: 30.0, n_muestra: 300, gl: 40}   # sobrescribe campos (nombres del §2)
  consulta: {nivel_pedido: departamento, rol: principal}
  contexto: {catalogo: {INEI-ENDES: {compuerta_ingesta: enlace_confirmado}}}   # opcional
  respuesta: null                # en reglas de respuesta: {cifras: [...], cruces: [...], texto: "..."}
  espera:
    dispara: true
    accion: publicar_referencial  # después de normalizar
    motivo: precision             # opcional
    modo: null                    # opcional
```

- Cada caso corre **solo su regla**: aplica_a, normalización y `CampoFaltante`.
- Un caso con `regla: PIPELINE` corre las etapas 0–7 y compara `espera.accion_final` y `espera.estado_cifra` (precedencia R-MOTOR-02).
- `base` es opcional: sin ella, la cifra lleva solo los campos del caso.
- Si `p`, `estimacion` o `n_sin_ponderar` no se dan explícitamente, se derivan de `valor` y `n_muestra` (§2c).
- Por regla, al menos: **un caso que dispara**, **uno que no** y, si la regla tiene umbrales, **los bordes** (el valor exacto del umbral).

Además de `accion`, `motivo`, `modo` y `objetivo`, el ejecutor compara `espera.nivel_minimo` y `espera.semaforo` (color en el detalle de R-CRUCES-09 o R-CRUCES-10).

**Pasos de degradación (`siguiente_paso` de R-MOTOR-01):** `{"tipo": "nivel", "nivel", "territorio_id"}`, `{"tipo": "agrupar", "anios": [desde, hasta]}`, combinado `{"tipo": "nivel_agrupar", ...}` y `{"tipo": "respuesta_parcial"}` (gasto). En una regla de respuesta, un campo faltante produce `revision_humana` sobre la respuesta, no la suprime.

**Contexto adicional:** `ctx.ambitos` (`dim_ambito`) y `ctx.tema_gasto` (`dim_tema_gasto`).

Si un caso necesita un campo que no está aquí, el analista lo usa con el nombre del diccionario de campos de `reglas.json` (`campos`) y lo anota en `campos_nuevos` del informe.
