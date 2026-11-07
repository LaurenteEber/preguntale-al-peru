# S3-09 — Empaquetado: imagen y `pap servir`

**Se deriva de P-05 y `stack.md`** (imagen Docker desde `uv.lock`; despliegue en el slice 4).

## Tareas

1. **`pap servir`:**
   - `--puerto` y `--red-local` (escucha en la red de la casa; por defecto, solo `127.0.0.1`);
   - imprime la dirección;
   - mensajes en `cli.yaml`.
2. **Imagen** (`Dockerfile` en la raíz):
   - Base `python:3.12-slim` más `curl` y `zstd` (`apt-get install --no-install-recommends`); `uv sync --frozen --no-dev`; usuario sin privilegios.
   - Al arrancar: `scripts/bajar_biblioteca.sh` si falta la biblioteca (o un volumen montado), y luego `uv run --frozen --no-dev pap servir`.
     - El script tiene `zstd` y no usa el camino de Python.
     - Si se toca el script para pasarle `--no-dev`, es un cambio mínimo con su prueba.
   - Clave del LLM solo por variable de entorno.
   - `HEALTHCHECK` con `python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:PUERTO/salud')"`.
   - `.dockerignore` sin crudos, `salidas/` ni `.venv`.
3. **Prueba:**
   - Si el entorno tiene Docker: construir, arrancar, pedir `/salud` y Q1.
   - Si no: se anota, y el dueño o el supervisor lo prueban en el Mac (`docker build` y `docker run`), con evidencia en `evidencia/s3-09_imagen.md`.
4. **Sin despliegue público** (P-05).

## Criterios de aceptación

- [x] `uv run pap servir` responde Q1 en un navegador local.
- [x] La imagen construye y responde `/salud` (evidencia de quien la probó).
- [x] Ningún crudo ni secreto en la imagen (`docker history` y lista de archivos).
