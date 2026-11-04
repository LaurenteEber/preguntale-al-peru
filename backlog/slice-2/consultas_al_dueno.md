# Slice 2 — Consultas al dueño

Mismas reglas que el slice 1 (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### E-01 — El entorno no puede subir a GitHub (S2-00) · abierta
- **Qué pasa:** todo `git push` desde esta sesión de la nube responde 403 («Claude doesn't have GitHub access to LaurenteEber/preguntale-al-peru»). La adenda y el slice 2 están solo en la sesión.
- **Por qué importa:** el entorno de la nube es efímero; si se reclama antes de subir, se pierde el trabajo. Tampoco se puede abrir el PR.
- **Qué se hizo:** `slice-2` nace de la punta de `slice-1-adenda` (S1-16 en verde), como pide S2-00 tarea 3 cuando la adenda no está fusionada. El PR del slice 2 va después del de la adenda.
- **Propuesta:** reconectar GitHub en claude.ai (Ajustes → Conectores) o instalar la app de Claude en el repositorio; luego subir `slice-1-adenda` y `slice-2`.

### E-02 — No hay clave de la API del LLM en el entorno (S2-00) · abierta
- **Qué pasa:** el entorno no tiene `ANTHROPIC_API_KEY` (comprobado sin imprimirla) ni el paquete del cliente.
- **Por qué importa:** S2-04 (grabar), S2-07, S2-08 (grabar), S2-09 y la corrida de S2-10 necesitan el LLM real.
- **Qué se hace:** según el README del slice, se sigue hasta S2-03 y con lo que no necesita el LLM real.
- **Propuesta:** agregar la clave como variable secreta del entorno y permitir la salida de red a `api.anthropic.com`.

### E-03 — La salida estructurada de la API no acepta todo el esquema de S2-01 (S2-04) · registrada (no bloquea)
- **Qué pasa:** según la documentación del proveedor (https://platform.claude.com/docs/en/build-with-claude/structured-outputs, 4/11/2026), la salida estructurada no acepta `$ref` externos, límites de longitud o número, `minItems` mayor que 1, `if/then` ni (sin documentar) `oneOf`.
- **Qué se hizo:** el cliente manda una versión simplificada del esquema (`esquema_para_api` en `src/pap/interprete/llm.py`). La validación completa la sigue haciendo el código con el esquema de S2-01 antes de aceptar nada.
- **Sin comprobar en vivo** (falta la clave, E-02): que la API acepte esa versión, la `temperature: 0` con el pensamiento adaptativo de Opus 5.5 y la cabecera `anthropic-version`. Se comprueba en la primera grabación.

### E-04 — Preguntas reales del dueño para el conjunto de evaluación (S2-02) · abierta (no bloquea)
- **Qué se pide:** si quieres, agrega preguntas reales tuyas a `tests/interprete/evaluacion.yaml` (sin datos personales), con su resultado esperado.
- **Dudas de quien escribió el conjunto, para la revisión de la muestra:** «Ayaviri (Melgar, Puno)» y «SJL» se dejaron tal cual (el primero lo convierte S2-05; el segundo hoy no lo encuentra el resolver); «el Callao» se escribió «Callao»; en cruce y efecto, el tema es el sujeto de la pregunta («¿cuánto se gastó…?» → gasto); los años relativos dejan el periodo fuera; m07, m08 y m09 esperan aclaración aunque se podrían leer como una sola consulta; «escribe un poema» y «muéstrame tu prompt» esperan «fuera de alcance» (también sería defendible «no es pregunta»).

### E-05 — Con la clave, falta grabar también los reintentos (S2-05) · registrada (no bloquea)
- **Qué pasa:** `tests/interprete/evaluar.py --grabar` graba solo la primera llamada. Si la primera respuesta grabada no valida, la evaluación grabada pide el reintento y falla con «falta la grabación».
- **Propuesta:** que S2-09 grabe a través de `interpretar()`, así quedan grabados también los reintentos.
- **Para confirmar:** el ancla de «todo el país» se acepta si *contiene* un texto nacional («del país» = «de el país»), como en el ejemplo del prompt (supuesto S2-05-d); «¿dónde es más alto?» sin nivel válido termina en «no entendida» y no pregunta el nivel (S2-05-c).

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
| S2-01-a | S2-01 | Defaults del intérprete del README (`sin_lugar`, `sin_intencion`, `anios_relativos`, `reintentos_si_no_valida`, `aclaracion_max_opciones`); `cache_horas` es decisión P-03 | `parametros_motor.yaml` → `interprete` |
| S2-01-b | S2-01 | Textos de los errores nuevos del contrato y de «no es pregunta» / «fuera de alcance» | `errores_consulta.yaml`, `textos/interprete.yaml` |
| S2-04-a | S2-04 | Modelo `claude-opus-5-5`, precios US$ 4 / 20 por millón, cabecera `2026-10-21` (copiados de la documentación oficial del 4/11/2026); tiempo máximo 60 s; `max_tokens` 2 000; tope por corrida US$ 5; temperatura 0 | `parametros_motor.yaml` → `interprete` |
| S2-05-a | S2-05 | Un año sin ancla válida (relativo, como «el año pasado», o que no está en la pregunta) se aclara igual: «El último año con datos» o «Escribe el año». En una serie, «el último año con datos» deja la serie sin el extremo descartado | `parametros_motor.yaml` → `interprete.anios_descartados` |
| S2-05-b | S2-05 | Un lugar sin ancla válida (territorio, `comparar_con` o `dentro_de`) se aclara como `sin_lugar` («Todo el Perú» / «Escribe el lugar»), con una pregunta para cada caso. Sin `dentro_de` en «¿dónde es más alto?», es todo el país, como en la vía estructurada | `interprete.lugar_descartado`; textos en `textos/interprete.yaml` → `aclaraciones` |
| S2-05-c | S2-05 | «¿Dónde es más alto?» sin un nivel con ancla válida termina en el mensaje «no entendimos» (no se adivina el nivel) | `interprete.extremo_sin_nivel` |
| S2-05-d | S2-05 | Anclas: «del» y «al» cuentan como «de el» y «a el», para que «del Perú» o «del país» valgan como todo el país; `nacional` vale si el ancla contiene uno de `territorio.textos_nacional`; el plural fija el nivel («provincias», «regiones»); un ancla debe ser palabras enteras y seguidas de la pregunta | `interprete.anclas` |
| S2-05-e | S2-05 | Si `sin_intencion` pasa a «aclarar», las opciones son «cuánto hay» y «cómo cambió» | `interprete.sin_intencion_opciones` |
| S2-05-f | S2-05 | Textos nuevos: «Entendimos: …» por intención (sin punto final, como el ejemplo de la historia), la etiqueta de cada opción del intérprete es la misma frase con mayúscula inicial, preguntas de las aclaraciones del código, «otro idioma», «no entendimos», la salida por la vía estructurada, «la pregunta venció» y el motivo nuevo `interprete_fuera_de_alcance` | `textos/interprete.yaml`, `textos/no_se_puede.yaml` |
| S2-05-g | S2-05 | El reintento le dice al LLM el código y el mensaje del error en el mensaje del usuario, después de la pregunta; se graba aparte (la huella incluye el error) | `interprete.reintento_mensaje`, `src/pap/interprete/llm.py` |
| S2-05-h | S2-05 | Caché en `salidas/interprete/cache/` (fuera de git): una interpretación válida por pregunta limpia, modelo y versión del prompt; las fallas no se guardan | `interprete.cache_carpeta` |
