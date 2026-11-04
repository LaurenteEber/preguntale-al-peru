# S3-00 — Preparación

## Tareas

1. **Entorno y base:**
   - `uv sync`;
   - en la nube, `bash scripts/bajar_biblioteca.sh`;
   - `uv run pytest -q -m "not solo_mac" > backlog/slice-3/evidencia/pytest_base.txt`.

   Crear `backlog/slice-3/consultas_al_dueno.md` y `evidencia/`.
2. **Lo aprendido en el slice 2:**
   - Leer `../slice-2/evidencia/cierre.md` y anotar en el README de este slice la latencia del LLM (p50 y p95), el costo por pregunta y los riesgos de P-03 que quedaron.
   - Con esa latencia se fija el objetivo del texto libre de S3-08 (`supuesto: S3-08`).
3. **Interfaces del slice 2 que usa la web** (anotar en `evidencia/s3-00_interfaces.md`, con archivo y línea):

   | Qué se necesita | Dónde se busca | Si falta |
   |---|---|---|
   | Firma de `interpretar()` y cómo recibe un LLM falso o grabaciones y la carpeta de la caché | `src/pap/interprete/` | Adaptador en `src/pap/web/` que no cambie su comportamiento (tipo A) |
   | Forma del tipo `mensaje`: si trae un código (`no_disponible`, `no_entendida`…) | `respuesta.json` de cada fila de la tabla de S2-06 | Agregar el campo `codigo` en el intérprete, sin cambiar textos (tipo A) |
   | Filas nuevas de `cli.codigo_salida` | `parametros_motor.yaml` | Se leen tal cual |

4. **Bases del slice 2 al cambiar el motor** (S3-01 y S3-02):
   - `slice-2/evidencia/base_estructurada/` y los reportes de evaluación son **evidencia histórica**: no se regeneran.
   - Las **pruebas permanentes** del slice 2 que comparen contra archivos fijos se listan aquí. S3-01 y S3-02 las actualizan con la misma aprobación del dueño que el cambio que las mueve.

## Criterios de aceptación

- [ ] `pytest_base.txt`, `s3-00_interfaces.md` y la lista del punto 4 guardados.
