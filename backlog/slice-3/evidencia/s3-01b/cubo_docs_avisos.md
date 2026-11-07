# S3-01b · filas 8 (script), 10, 11 y 13 — cubo, documentación y avisos

## Fila 8 · `scripts/comprobar_enlaces.sh`
Lista el código HTTP de cada enlace que el motor puede poner en una cita (mismas reglas que `_url` de `capas.py`: `url` de las doradas; si no, `url_portal` o `url_datos` de la fuente en el catálogo; sin repetidos). Usa `curl -sS -L --max-time 20` sin `-k`: un certificado vencido cuenta como falla. Sale con error si algún código no es 2xx/3xx. Salida del 6/11/2026: `enlaces.txt`.

Resultado: 34 enlaces, 28 con 200 y 6 con falla:
- 5 enlaces de `datosabiertos.gob.pe` dan **418**. Con un `User-Agent` de navegador el mismo enlace da 200 (probado con uno): el portal rechaza a `curl` a secas. No se cambió el comando pedido; propuesta: agregar `-A 'Mozilla/5.0'` (decisión del dueño).
- `portales.reniec.gob.pe/web/estadistica/identificada` da **000**: certificado vencido del portal de RENIEC (`curl: (60)`). Es una falla real del enlace, no del script.
- El enlace del SIEN (colección de gob.pe) da 200.

## Fila 10 · el cubo local debe ser el del manifiesto
- `tests/conftest.py`: `discrepancia_cubo(raiz)` compara el sha256 de `biblioteca/indicadores/fact_indicador.parquet` con `tablas.fact_indicador.hash` del manifiesto; `pytest_sessionstart` detiene la sesión (código 3) con un solo mensaje, antes de cualquier prueba: «el cubo local no es el del manifiesto: corre `pap calcular`». Si falta el cubo o el manifiesto no aborta (fallan por sí solas las pruebas que lo necesitan).
- `tests/test_cubo_manifiesto.py` (6 pruebas): el mensaje exacto; cubo distinto → mensaje; cubo igual → nada; cubo ausente → nada; la sesión se detiene con ese mensaje; el cubo real coincide con el manifiesto.
- Rojo primero: antes de implementar, la colección falló con `ImportError: cannot import name 'MENSAJE_CUBO_DISTINTO' from 'conftest'`. Después: 6 pasan.
- Simulación de cubo distinto, sin tocar `biblioteca/`: una copia temporal con un cubo falso y el manifiesto real dio `Exit: el cubo local no es el del manifiesto: corre `pap calcular``, sin correr ninguna prueba.
- `scripts/bajar_biblioteca.sh` y la guía (§1.1) dicen que, después de bajar el release, hay que correr `pap calcular`.
- **Release:** `gh release list -R LaurenteEber/preguntale-al-peru` solo muestra `biblioteca-ba1fbc55` (Latest y un Draft). **No existe `biblioteca-010ea965`**: el valor por defecto del script sigue siendo `biblioteca-ba1fbc55`, con un comentario que lo explica. Falta publicar ese release (lo hace el dueño en el Mac).

## Fila 11 · documentación (un tema, un lugar)
- Guía: se quitó su §4 «Hacer una pregunta al motor» y enlaza al manual §3. Lo que no estaba en el manual se movió: el formato de la consulta del piloto en YAML, la ficha corta/larga y `resultados_respuesta`, y `--limite` de la matriz → manual; el mapa de comandos de mantenimiento (§3.7), «qué se puede cambiar» (§3.8) y la operación del intérprete (nuevo §4) → guía. Nueva §1.1 «Trabajar en local o en la nube».
- Manual: se quitó su §3.3 «Mantener la biblioteca de datos» y enlaza a la guía (§1.1, §3, §3.7); «Calidad» pasó a ser §3.3.
- Correcciones: estado del encabezado del manual remite a `estado.md`; slice 2 «cerrado el 5/11/2026 (PR #2)» en el manual y en `hoja_de_ruta.md`; el número de pruebas (748) se reemplazó por un enlace a `estado.md` en manual, `calidad.md` y `arquitectura.md`; enlace roto `arquitectura_y_funcionamiento.md` → `arquitectura.md`; se quitó «Versión al 13/10/2026»; huella actual `010ea965…` (guía, manual, `calidad.md`), apuntando al manifiesto.
- Queda sin tocar: `docs/estado.md` todavía dice «775 pruebas» y «748 pruebas en verde» (este último, histórico de la migración). Conviene actualizarlo al cerrar el slice.

## Fila 13 · avisos de pytest
`pyproject.toml` → `filterwarnings` con dos entradas por mensaje (comentadas): Starlette/httpx en `TestClient` y «Print area cannot be set to Defined name» de openpyxl. Sin dependencias nuevas. `uv run pytest -q tests/web tests/test_s4_insumos.py`: antes 2 avisos; ahora ninguno. (En esa corrida fallan 3 pruebas de equivalencia de `tests/web/test_servicio.py` porque otros escritores están cambiando textos de las respuestas —H-A— mientras se corría; no tienen relación con estos cambios.)
