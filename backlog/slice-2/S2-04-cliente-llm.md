# S2-04 — Limpieza, cliente del LLM, grabaciones y presupuesto

**Requiere X-12, X-13 y X-14.**

## Por qué

El LLM es la única parte no determinista y la única que cuesta por uso. Va detrás de una interfaz pequeña, se reproduce sin red en las pruebas y tiene tope de gasto. Lo que la persona escribe se limpia **antes** de que salga del equipo.

## Tareas

1. **Limpieza** (`src/pap/interprete/limpiar.py`), antes del LLM, de la caché, del registro y de `pregunta_original`:
   - Recortar a 1 000 caracteres (`maxLength` de `pregunta_original`) con un aviso fijo.
   - Quitar caracteres de control.
   - Reemplazar por `[dato personal]` los números con forma de DNI (8 dígitos), RUC (11), celular (9 dígitos que empiezan con 9) y los correos.
     - Los años de 4 cifras no se tocan.
     - Los patrones van en `interprete.datos_personales`, `decision: P-03`.
2. **Interfaz** (`src/pap/interprete/llm.py`): `interpretar_crudo(prompt, pregunta_limpia) -> RespuestaLLM`, con el JSON, el modelo, los tokens, la latencia y el costo estimado.
   - Implementación con **`httpx`**, que ya está en `uv.lock`. Si hiciera falta un SDK, es una consulta tipo C.
   - Salida estructurada con el esquema de S2-01, temperatura 0, y la pregunta como dato delimitado, fuera de las instrucciones.
   - **Modelo provisional** en `interprete.modelo` (`supuesto: S2-04`; el definitivo se elige en S2-09). Tiempo máximo y precios en `interprete`. Los precios se copian de la página oficial del proveedor, con fecha y enlace en `nota:`, no de memoria.
3. **Clave:** se lee de una variable de entorno, cuyo nombre va en `interprete.variable_clave`. Nunca se escribe en archivos, registros ni errores. Sin clave → `no_disponible` (S2-05).
4. **Grabaciones** (`tests/interprete/grabaciones/`):
   - Una por pregunta, con nombre = huella de (pregunta limpia, modelo, `version_prompt`).
   - Modo `reproducir`: el de siempre en pytest.
   - Modo `grabar`: un corredor mínimo, `tests/interprete/evaluar.py --grabar [--solo <ids>]`, que S2-09 amplía.
   - Si falta una grabación: «falta la grabación; corre `uv run python tests/interprete/evaluar.py --grabar --solo <id>`».
   - Solo se graban preguntas del conjunto y de las pruebas, nunca de usuarios.
5. **Uso y tope** (X-13):
   - Registro local en `salidas/interprete/uso.jsonl` (fuera de git), con los campos de X-14.
   - `interprete.tope_por_corrida` corta una corrida de evaluación.
   - El tope mensual real es el de la consola del proveedor. Si el proveedor responde que el límite se agotó → `no_disponible`.
6. **Pruebas** (`tests/interprete/test_llm.py`, sin red):
   - una grabación se reproduce byte a byte;
   - la clave de prueba no aparece en ningún archivo tras una corrida;
   - el tope corta la corrida;
   - tiempo agotado, límite agotado y falta de clave dan `no_disponible`;
   - DNI, celular y correo se reemplazan y los años no.

## Criterios de aceptación

- [ ] `uv run pytest -q` pasa con la red cortada y sin la variable de la clave.
- [ ] `uv.lock` sin cambios.
- [ ] `evaluar.py --grabar --solo` funciona en vivo con la clave (evidencia: una grabación de Q2).
