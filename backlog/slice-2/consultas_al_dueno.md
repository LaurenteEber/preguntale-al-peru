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

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
| S2-01-a | S2-01 | Defaults del intérprete del README (`sin_lugar`, `sin_intencion`, `anios_relativos`, `reintentos_si_no_valida`, `aclaracion_max_opciones`); `cache_horas` es decisión P-03 | `parametros_motor.yaml` → `interprete` |
| S2-01-b | S2-01 | Textos de los errores nuevos del contrato y de «no es pregunta» / «fuera de alcance» | `errores_consulta.yaml`, `textos/interprete.yaml` |
| S2-04-a | S2-04 | Modelo `claude-opus-5-5`, precios US$ 4 / 20 por millón, cabecera `2026-10-21` (copiados de la documentación oficial del 4/11/2026); tiempo máximo 60 s; `max_tokens` 2 000; tope por corrida US$ 5; temperatura 0 | `parametros_motor.yaml` → `interprete` |
