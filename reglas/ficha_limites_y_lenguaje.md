# Ficha de límites y reglas de lenguaje

Plantilla que acompaña cada respuesta (R-LENGUAJE-01). La genera el sistema desde el resultado del validador; el LLM no la redacta.

## Principios

- Se genera por plantilla desde el resultado del validador; el LLM no la redacta.
- Versión corta siempre visible bajo la respuesta (máx. 4 líneas); versión larga en un desplegable 'Límites de esta respuesta'.
- Una ficha por respuesta, con una sección por cifra principal y una por cruce; las cifras de contexto se listan en la versión larga.
- Los textos de 'qué NO se puede concluir' salen de una lista de códigos fijos, no de redacción libre.

## Versión corta (siempre visible)

| Campo | Texto |
|---|---|
| `semaforo_respuesta` | Confianza: {rotulo} — {motivo}. {si ambar/rojo y hay rango: 'La cifra real puede estar entre {inf} y {sup}.'} |
| `fuentes_anios` | Datos de: {lista 'SIGLA AÑO (entidad)' separada por ' · '} |
| `territorio` | Territorio: {nivel_respuesta} de {nombre}{si nivel_respuesta != nivel_pedido: ' (no {nivel_pedido}: ' + motivo_nivel_corto + ')'} |
| `no_concluir_principal` | No permite concluir: {hasta 2 códigos: NC-ACTUAL si está activo + el de mayor prioridad} |

**Ejemplo:**

```
Confianza: Dato con limitaciones — respondimos por departamento, no por provincia.
Datos de: ENDES 2025 (INEI) · Gasto MEF 2025 (devengado)
Territorio: departamento de Puno (la encuesta no alcanza para provincias)
No permite concluir: que el gasto haya causado los cambios en la anemia.
```

## Versión larga (desplegable)

### 1. De dónde vienen los datos

Plantilla: {nombre_fuente} ({entidad}), {periodo}. Es {naturaleza_ciudadana}. Datos descargados el {fecha_descarga}.

### 2. Territorio y por qué

Plantilla: Las cifras se presentan por {nivel_respuesta}. {motivo_nivel}. {texto_base_geografica}

**textos_base_geografica**

| Caso | Texto |
|---|---|
| `residencia` | Las personas se cuentan donde viven. |
| `establecimiento` | Se cuenta donde está el establecimiento que atendió, aunque la persona viva en otro distrito. |
| `ejecutora` | El gasto se ubica donde está la oficina que paga, no donde se usa el dinero; por eso solo lo mostramos por distrito en municipalidades y obras con ubicación registrada. |
| `meta_departamento` | El gasto se ubica en el departamento donde se usa el dinero; no se sabe en qué provincia o distrito. |
| `inversion_ubicacion` | La obra se ubica donde se registró en el banco de inversiones. |
| `muestra` | La encuesta entrevista a una muestra; solo da cifras con suficiente precisión para el departamento o áreas grandes. |
| `territorio` | Cifra referida a todo el territorio. |

### 3. Qué mide exactamente

Plantilla: Mide {tipo_medida_ciudadana} en {poblacion_objetivo}{si universo != total: ', solo ' + universo}. {nota_criterio}

**textos_tipo_medida**

| Caso | Texto |
|---|---|
| `prevalencia` | cuántas personas de la población tienen la condición |
| `cobertura_programa` | cuántas personas o hogares están inscritos o reciben el programa |
| `atenciones_produccion` | cuántas atenciones se dieron (una persona puede tener varias) |
| `notificacion_vigilancia` | cuántos casos llegaron a ser detectados y reportados por los servicios |
| `registro_eventos` | cuántos hechos se registraron (nacimientos, defunciones, etc.) |
| `presupuesto_gasto` | cuánto dinero se gastó o asignó |
| `estimacion_modelada` | un cálculo con un modelo estadístico, no un conteo directo |
| `stock_infraestructura` | qué infraestructura existe y en qué estado |
| `padron_referencia` | un listado de referencia |

### 4. Qué tan precisa es

Plantilla: {rotulo}. {si encuesta: 'El valor real está probablemente entre {ic_inf} y {ic_sup}.'} {si registro: 'Basado en {numerador_redondeado} casos registrados' (con numerador < umbral de R-REG-12: 'menos de {umbral} casos')} {motivos_semaforo en texto}

### 5. Cambios de método y comparaciones

Plantilla: {si quiebre: 'En {anio} cambió {motivo}: no comparamos antes y después directamente.'} {si comparación: 'Entre {a} y {b}: {cambio_significativo\|sin cambio estadísticamente claro}.'} {si pooling: 'Se juntaron los años {periodo} para tener suficientes casos.'}

### 6. Cruces y asociaciones

Plantilla: Se compararon {N} {nivel_cruce}s ({excluidos} sin datos suficientes). {texto_asociacion}. Esto compara territorios, no personas, y no muestra causas.

### 7. Qué NO se puede concluir

Plantilla: —

**codigos_no_concluir**

| Caso | Texto |
|---|---|
| `NC-CAUSA` | Que {a} haya causado {b}: estos datos no comparan con lo que habría pasado sin el programa o gasto. |
| `NC-INDIVIDUO` | Que lo que pasa entre territorios ocurra igual entre personas u hogares. |
| `NC-NIVEL` | Nada sobre provincias o distritos concretos: la fuente solo da cifras con suficiente precisión para {nivel_publicado}. |
| `NC-RANKING` | Un orden exacto entre territorios: las diferencias entre muchos de ellos no son estadísticamente claras. |
| `NC-ACTUAL` | Cuál es la situación hoy: el dato es de {anio_dato}{si choque: ', antes de la pandemia'}. |
| `NC-TAMIZADOS` | Cuántos niños del distrito tienen anemia: solo sabemos de los que se tamizaron en establecimientos. |
| `NC-GASTO-LUGAR` | Cuánto se gastó dentro de cada distrito: el gasto de ministerios y gobiernos regionales no se registra por distrito. |
| `NC-EFICIENCIA` | Si el gasto fue eficiente o 'cuánto costó' reducir el problema. |
| `NC-TENDENCIA-QUIEBRE` | Si el indicador subió o bajó entre {a} y {b}: cambió la forma de medirlo. |
| `NC-ATENCIONES-PERSONAS` | Cuántas personas distintas fueron atendidas: una persona puede tener varias atenciones. |

**prioridad_codigos**

- NC-CAUSA
- NC-ACTUAL
- NC-NIVEL
- NC-TAMIZADOS
- NC-GASTO-LUGAR
- NC-TENDENCIA-QUIEBRE
- NC-INDIVIDUO
- NC-RANKING
- NC-EFICIENCIA
- NC-ATENCIONES-PERSONAS

**reglas_asignacion**

| Caso | Texto |
|---|---|
| `NC-CAUSA` | siempre que haya gasto o programa y un resultado en la misma respuesta |
| `NC-INDIVIDUO` | siempre que haya asociación entre territorios |
| `NC-NIVEL` | nivel_respuesta > nivel_pedido, o cifra principal de encuesta muestral publicada por departamento, ámbito de Lima o nacional cuando ningún otro código aplica (C-04, 3/11/2026) |
| `NC-ACTUAL` | criterio vigencia >= 1 |
| `NC-TAMIZADOS` | fuente INS-CENAN-SIEN |
| `NC-GASTO-LUGAR` | gasto con base ejecutora o meta_departamento |
| `NC-RANKING` | comparación de >=3 territorios |
| `NC-TENDENCIA-QUIEBRE` | R-CRUCES-04 activada |
| `NC-ATENCIONES-PERSONAS` | tipo_medida=atenciones_produccion |
| `NC-EFICIENCIA` | intencion_pregunta=efecto |

### 8. Reproducibilidad

Plantilla: Cálculo del {fecha} con catálogo v{v_cat} y reglas v{v_reglas}. Indicadores: {ids}.

### ejemplo_relleno

```json
{
 "pregunta": "¿Cuánta anemia hay en la provincia de Azángaro y cuánto se gasta en combatirla?",
 "corta": "Confianza: Dato con limitaciones — respondimos por departamento, no por provincia.\nDatos de: ENDES 2025 (INEI) · SIEN 2025 (INS) · Gasto MEF 2025\nTerritorio: departamento de Puno (la encuesta no alcanza para provincias)\nNo permite concluir: que el gasto haya causado los cambios en la anemia.",
 "larga_resumen": [
  "1. ENDES 2025: encuesta a una muestra de hogares; SIEN 2025: registro de niños tamizados en establecimientos; MEF: gasto devengado del PPoR 1001 ubicado por DEPARTAMENTO_META.",
  "2. Departamento: la ENDES solo es confiable por departamento; el gasto regional y nacional solo se ubica por departamento. Para Azángaro solo se muestra el SIEN provincial (tamizados) y el gasto de sus municipalidades.",
  "3–4. Anemia en niños de 6 a 35 meses (ENDES, verde); proporción de tamizados con anemia (SIEN, ámbar).",
  "5. Criterio de anemia OMS 2024 desde 2024: no se compara con años previos salvo con el mismo criterio.",
  "7. No se puede concluir: NC-CAUSA, NC-NIVEL, NC-TAMIZADOS, NC-GASTO-LUGAR."
 ]
}
```

### ayuda_confianza

```json
"La confianza indica si hay suficientes datos y si son recientes. No indica qué causó el problema."
```

## Lenguaje

### Expresiones permitidas

| Expresión | Uso |
|---|---|
| se estima que / alrededor de | encuestas y estimaciones modeladas |
| el valor real está probablemente entre X y Y | rango probable (IC 95 %); preferir a 'margen de error' |
| según {fuente} {año} | toda cifra |
| aumentó / disminuyó de forma estadísticamente clara | solo con test_cambio.significativo=true (p<0,05) |
| se mantuvo sin cambio estadísticamente claro / en general estable | test no significativo |
| está en el grupo de departamentos con niveles más altos (o más bajos) | rankings por grupos estadísticamente semejantes (método INEI) |
| los territorios con más X tienden a tener más/menos Y | asociación con IC que excluye 0 |
| no se observa una asociación clara | IC de rho incluye 0 |
| en el mismo periodo / por otro lado / en paralelo | conectar cifras de fuentes distintas |
| se registraron / se atendieron / se tamizaron / se notificaron | registros administrativos |
| se gastó (devengado) / se asignó (PIM) / registrado por unidades ejecutoras con sede en | gasto |
| en {año} se estimaba | datos con más de 2 años |
| estos datos no permiten saber si | límites causales |
| con los datos públicos que usamos no se puede responder | falta de datos |
| según la evaluación de {entidad} ({año}) | citar evaluaciones curadas |

### Patrones prohibidos (los revisa un corrector automático)

| Categoría | Patrón | Reemplazo | Excepción |
|---|---|---|---|
| causal | `\b(caus(o\|a\|an\|aron\|ado)\|provoc(o\|a\|an\|aron\|ado)\|origin(o\|aron)\|desencaden(o\|a)\|incidi(o\|eron)\|repercuti(o\|eron)\|permiti(o\|eron) (reducir\|bajar\|mejorar\|aumentar\|disminuir)\|ayud(o\|aron) a (reducir\|bajar\|mejorar\|disminuir)\|se (explica\|debe) (por\|a)\|es (consecuencia\|resultado\|producto) de\|a raiz de\|producto de\|tras la implementacion)\b` | — | — |
| causal | `\b(gracias\|debido\|por efecto\|como resultado\|como consecuencia) (a\|al\|a la\|a los\|a las\|del\|de la\|de los)\b\|\b(por eso\|por ello\|por lo tanto\|por esta razon\|por consiguiente\|lo que explica\|en consecuencia\|asi que)\b` | — | — |
| causal/evaluativa | `\b(impacto\|efecto)s? (positivo\|negativo\|de(l)?\|que tuvo)\b\|\b(sirvi(o\|eron)\|funcion(o\|aron)\|fue (eficaz\|efectiv[oa]\|un exito\|un fracaso)\|logr(o\|aron) (reducir\|bajar\|mejorar\|disminuir)\|contribuy(o\|eron) a\|redujo\|reduce\|reducira)\b` | — | — |
| ranking puntual | `\b(el\|la\|los\|las) (peor(es)?\|mejor(es)?) (region\|regiones\|departamento\|departamentos\|provincia\|provincias\|distrito\|distritos\|municipalidad\|municipalidades\|gobierno\|gobiernos\|entidad\|entidades\|alcalde\|alcaldes\|gestion\|gestiones\|lugar\|posicion\|ejecutor\w*)\b\|\b(es\|son\|fue\|fueron) (el\|la\|los\|las) (peor(es)?\|mejor(es)?)\b\|\b(el\|la) (region\|departamento\|provincia\|distrito\|municipalidad\|gobierno regional\|entidad)\b[^.]{0,30}\bmas (pobre\|rico\|alto\|alta\|bajo\|baja\|afectad[oa])\b\|\b(es\|son) (el\|la\|los\|las) (que )?(mas\|menos)\b\|\bencabeza\|\blider(a\|an)\b\|\b(primer\|ultimo\|segundo\|tercer) (lugar\|puesto)\b\|\branking\b\|\btop\b\|\bpuesto (n\|\d)\|\b(el\|la) (peor\|mejor) \w+ (del\|de la\|de los) (peru\|pais\|region\|departamento\|provincia)\b\|\b(el\|la\|los\|las) que (peor\|mejor)\b\|\b(peor\|mejor) (gasta\|gastan\|ejecuta\|ejecutan\|invierte\|invierten)\b` | — | — |
| cambio sin significancia | `\b(aument\w*\|disminu\w*\|se reduj\w*\|se reduc\w*\|se redujo\|baj(ó\|aron\|ará\|arán)\|sub(ió\|ieron\|irá\|irán\|e\|en)\|crec(ió\|ieron\|e\|en\|erá\|erán)\|cay(ó\|eron)\|cae(n\|rá\|rán)?\|mejor(ó\|aron\|ará\|arán)\|empeor\w*\|descend\w*\|retroced\w*\|se elev\w*\|se increment\w*\|repunt\w*\|se dispar\w*\|se desplom\w*)\b\|\bpas(ó\|aron) de\b[^.]{0,40}\ba\b\|\b(una\|un\|la\|el) (reducción\|disminución\|caída\|aumento\|incremento\|alza\|subida\|descenso)\b\|\b(ha\|han\|había\|habían) (aumentado\|disminuido\|bajado\|subido\|reducido\|caído\|mejorado\|empeorado\|crecido\|descendido)\b` | — | — |
| falsa certeza | `\b(exactamente\|con (toda )?(certeza\|seguridad)\|esta (demostrado\|comprobado)\|(se )?ha (demostrado\|comprobado)\|sin (ninguna )?duda\|definitivamente\|indudablemente\|obviamente\|es evidente\|es un hecho\|la verdad es\|claramente)\b` | — | — |
| juicio de valor | `\b(despilfarr\w*\|derroch\w*\|malgast\w*\|desperdici\w*\|mal (uso\|gasto\|manejo)\|negligen\w*\|fracas\w*\|culpa\w*\|responsable de\|pesim\w*\|deficiente\|ineficien\w*\|incapa\w*\|mala gestion\|buena gestion\|excelente\|exitos\w*\|ejemplar\|alarmante\w*\|preocupante\w*\|escandalos\w*\|vergonzos\w*\|dramatic\w*\|lamentable\w*\|irresponsab\w*)\b` | — | — |
| acusación o atribución a personas | `\b(alcalde\|alcaldesa\|gobernador\|gobernadora\|ministro\|ministra\|congresista\|funcionario\|autoridad(es)?\|gestion (del\|de la) (alcalde\|gobernador))\b[^.]{0,60}\b(rob\w*\|malvers\w*\|coim\w*\|corrupt\w*\|responsable\w*\|culpa\w*\|hizo\|logro\|fallo\|abandon\w*\|descuid\w*)` | — | — |
| predicción | `\b(alcanzar\|llegar\|aumentar\|subir\|bajar\|disminuir\|crecer\|mejorar\|empeorar\|reducir\|caer\|cambiar)(a\|an)\b\|\bhabra\b\|\bse espera que\b\|\bse proyecta\b\|\bva(n)? a (subir\|bajar\|aumentar\|disminuir\|mejorar\|empeorar\|llegar\|alcanzar\|ser)\b\|\bseguira (subiendo\|bajando\|aumentando\|disminuyendo)\b` | — | — |
| falacia ecológica | `\b(los\|las) (ninos\|ninas\|hogares\|familias\|beneficiari[oa]s\|usuari[oa]s\|personas\|afiliad[oa]s\|estudiantes)\b[^.]{0,60}\b(tienen\|son\|viven\|estan\|presentan\|logran)\b[^.]{0,20}\b(mas\|menos\|mejor\|peor)\b` | — | — |
| gasto mal ubicado | `\b(gast(o\|aron\|a)\|invirti(o\|eron)\|ejecut(o\|aron)\|destin(o\|aron))\b[^.]{0,30}\ben el distrito\b` | — | — |
| ambigüedad | `(?<!estadisticamente )\bsignificativ(o\|a\|os\|as\|amente)\b(?! estad)` | — | — |
| juicio de valor | `\b(mala\|buena)s? ejecutoras?\b\|\b(municipalidad\w*\|municipios?\|gobiernos? (regional\|regionales\|local\|locales\|nacional)\|gores?\|ministerios?\|ejecutoras?\|pliegos?\|entidad(es)?\|region(es)?\|alcaldias?\|diresas?\|ugel(es)?)\b[^.;]{0,40}\bno (supo\|supieron) (gastar\|ejecutar)\b\|\bno (supo\|supieron) (gastar\|ejecutar) (el\|su\|sus\|los) (presupuesto\|recursos\|fondos)\b\|\bincapacidad de (gasto\|gastar\|ejecucion\|ejecutar)\b\|\b(municipalidad\w*\|municipios?\|gobiernos? (regional\|regionales\|local\|locales\|nacional)\|gores?\|ministerios?\|ejecutoras?\|pliegos?\|entidad(es)?\|region(es)?\|alcaldias?\|diresas?\|ugel(es)?)\b[^.;]{0,40}\bdej(o\|aron) de (gastar\|ejecutar)\b\|\bdevolvi(o\|eron) (el\|la\|los\|las\|su\|sus) (dinero\|presupuesto\|recursos\|fondos\|plata)\b\|\bdevolvi(o\|eron)\b[^.;]{0,40}\bal tesoro\b\|\bperdi(o\|eron) (el\|la\|los\|las\|su\|sus) (presupuesto\|recursos\|fondos)\b\|\bse perdi(o\|eron)\b[^.;]{0,40}\b(del\|de su\|de sus\|de los) (presupuesto\|recursos\|fondos)\b\|\b(presupuesto\|recursos\|fondos)\b[^.;]{0,30}\bse perdi(o\|eron)\b\|\b(municipalidad\w*\|municipios?\|gobiernos? (regional\|regionales\|local\|locales\|nacional)\|gores?\|ministerios?\|ejecutoras?\|pliegos?\|entidad(es)?\|region(es)?\|alcaldias?\|diresas?\|ugel(es)?)\b[^.;]{0,40}\bperdi(o\|eron)\b[^.;]{0,30}\b(millones\|soles\|dinero\|presupuesto\|recursos\|fondos)\b\|\bsobr(o\|aron)\b[^.;]{0,30}\b(presupuesto\|recursos\|fondos)\b\|\b(presupuesto\|recursos\|fondos)\b[^.;]{0,30}\bsobr(o\|aron)\b\|\b(municipalidad\w*\|municipios?\|gobiernos? (regional\|regionales\|local\|locales\|nacional)\|gores?\|ministerios?\|ejecutoras?\|pliegos?\|entidad(es)?\|region(es)?\|alcaldias?\|diresas?\|ugel(es)?)\b[^.;]{0,40}\b(le \|les )?sobr(o\|aron)\b\|\bles? sobr(o\|aron)\b[^.;]{0,20}\b(millones\|soles)\b\|\bbaja capacidad de ejecucion\b\|\bes normal que no se (gaste\|gasten\|ejecute\|ejecuten)\b` | — | — |
| nombre de programa vencido | `(?:^\|[.;])(?=[^.;]*(?:\b(?:gastos?\|presupuestos?\|ejecuci[oó]n\|devengados?\|inversi[oó]n\|lo ejecutado\|lo gastado\|lo devengado)(?: total)? (?:del\|en el\|por el) (?:\b(?-i:PAN)\b\|programa articulado nutricional)(?!\s*(?:entre (?:19\|20)\d\d y \|de (?:19\|20)\d\d a \|hasta \|\(\s*(?:19\|20)\d\d\s*[–-]\s*\|(?:19\|20)\d\d\s*[–-]\s*)(?:19\d\d\|20(?:0\d\|1\d\|2[0-2]))\b)\|\bel (?:\b(?-i:PAN)\b\|programa articulado nutricional) (?:gast[oó]\|ejecut[oó]\|deveng[oó]\|invirti[oó]\|recibi[oó]\|cost[oó]\|tuvo)\b\|\bse (?:gast[oó]\|gastaron\|ejecut[oó]\|ejecutaron\|invirti[oó]\|invirtieron\|destin[oó]\|destinaron)\b[^.;]{0,40}\ben el (?:\b(?-i:PAN)\b\|programa articulado nutricional)))[^.;]*(?<!desde )(?<!partir de )(?<!despues de )(?<!después de )\b20(?:2[3-9]\|[3-9]\d)\b` | — | — |

### redondeo

```json
[
 {
  "tipo": "porcentaje de encuesta, semáforo verde",
  "regla": "1 decimal",
  "ejemplo": "20,2 %"
 },
 {
  "tipo": "porcentaje de encuesta, ámbar/referencial",
  "regla": "entero, con 'alrededor de' y rango",
  "ejemplo": "alrededor de 47 % (entre 42 % y 52 %)"
 },
 {
  "tipo": "estimación modelada con IC > 20 pp",
  "regla": "solo intervalo en enteros",
  "ejemplo": "entre 31 % y 55 %"
 },
 {
  "tipo": "tasa de registros (por 1 000 o 100 000)",
  "regla": "1 decimal; entero si numerador < 20",
  "ejemplo": "12,4 por 1 000 nacidos vivos"
 },
 {
  "tipo": "conteo de registros",
  "regla": "exacto hasta 9 999; desde 10 000 en miles con 1 decimal",
  "ejemplo": "1 234 / 12,3 mil"
 },
 {
  "tipo": "monto de gasto",
  "regla": ">= S/ 1 millón: millones con 1 decimal; < 1 millón: miles enteros; per cápita: soles enteros; indicar nominal o constante y año base",
  "ejemplo": "S/ 245,7 millones (soles corrientes)"
 },
 {
  "tipo": "población",
  "regla": "miles con 1 decimal; >= 1 millón: millones con 2 decimales",
  "ejemplo": "35,4 mil habitantes; 1,23 millones"
 },
 {
  "tipo": "coeficiente de asociación",
  "regla": "no mostrar el número en la versión corta; versión larga 2 decimales con IC",
  "ejemplo": "rho = −0,42 (entre −0,70 y −0,04)"
 },
 {
  "tipo": "valores muy pequeños",
  "regla": "porcentaje < 0,5 → 'menos de 1 %'",
  "ejemplo": "menos de 1 %"
 }
]
```

### citas

```json
{
 "corta_en_texto": "({sigla} {año}, {entidad})",
 "primera_mencion": "nombre completo + sigla",
 "gasto": "(MEF, Consulta amigable/datos abiertos, devengado {año}, actualizado al {fecha})",
 "evaluacion": "según la evaluación {tipo} de {entidad} ({año})"
}
```

### frases_estandar

```json
{
 "sin_datos": "Con los datos públicos que usamos no se puede responder {parte} para {territorio} porque {motivo}.",
 "alternativa": "Lo más cercano que sí podemos mostrar es: {alternativa}.",
 "fuera_alcance": "Esta pregunta pide {tipo} y Pregúntale al Perú solo responde con cifras públicas agregadas por territorio. Puedes preguntar sobre: {temas}.",
 "efecto": "Saber si un gasto o programa funcionó requiere una evaluación que compare con lo que habría pasado sin él. Estos datos muestran qué se gastó y cómo cambió el indicador, pero no si uno causó lo otro.",
 "asociacion": "Esto compara territorios, no personas: no dice que una cosa cause la otra.",
 "dato_antiguo": "Dato de {año}, anterior a la pandemia: la situación actual probablemente es distinta."
}
```

### notas_corrector

```json
"B18, B19 y B27 (presente con dato antiguo, tamizados como prevalencia) no son detectables de forma fiable por regex: requieren verificar la oración que contiene cada marcador {{c:id}} contra sus metadatos (edad del dato, tipo_medida). La lista está ajustada a este corpus: validar con un corpus de reserva antes de adoptarla."
```

### avisos_pendientes_validacion

```json
[
 {
  "categoria": "causal (ampliación, ajustado)",
  "patron": "\\bexplica(n|ria|rian)? (por que|(buena |gran |la mayor )?parte de|(el|la|los|las) (menor|mayor|baja|alta|caida|reduccion|aumento|mejora|disminucion|descenso))\\b|\\bdesde que (llego|llegaron|se (implemento|aplico))\\b|\\b(desde|con|tras) la (llegada|implementacion|puesta en marcha) de",
  "efecto": "aviso: se informa, no bloquea la consolidación ni la respuesta",
  "estado": "pendiente validación por terceros",
  "origen": "auditoría independiente r4 (aud_mensajes/patrones_ajustados.json); decisión del orquestador 7/10/2026"
 },
 {
  "categoria": "precisión excesiva (ajustado)",
  "patron": "\\d,\\d{3,}|\\d[.,]\\d{2,} ?(%|por ciento)|s/ ?\\d[\\d ]*,\\d{2,}",
  "efecto": "aviso: se informa, no bloquea la consolidación ni la respuesta",
  "estado": "pendiente validación por terceros",
  "origen": "auditoría independiente r4 (aud_mensajes/patrones_ajustados.json); decisión del orquestador 7/10/2026"
 },
 {
  "categoria": "juicio de valor (ampliación, ajustado)",
  "patron": "\\b(mala|buena|pesima|peor|mejor)s? ejecutora|(?:^|[.;:]) ?(?![^.;:]*\\bsi\\b)[^.;:]*\\b(gasta|gastan|ejecuta|ejecutan) (muy )?(mal|bien)\\b|\\b(baja|alta|poca|mucha|buena|mala) capacidad de gasto\\b",
  "efecto": "aviso: se informa, no bloquea la consolidación ni la respuesta",
  "estado": "pendiente validación por terceros",
  "origen": "auditoría independiente r4 (aud_mensajes/patrones_ajustados.json); decisión del orquestador 7/10/2026"
 }
]
```
