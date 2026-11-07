# S3-09 — Evidencia de la imagen y de `pap servir`

Probado el 6/11/2026 en el Mac del dueño (Docker 29.5.2 con colima, arm64). Imagen: `pap-s3-09:local`.

## Construir

```bash
docker build -t pap-s3-09:local .
docker images pap-s3-09     # 1,34 GB en disco (308 MB comprimida)
```

Qué pesa: base `python:3.12-slim` ≈ 160 MB; `curl`, `zstd` y uv ≈ 59 MB; entorno `uv sync --frozen --no-dev --no-cache` ≈ 807 MB (DuckDB, pandas, pyarrow, svy…); código y curados ≈ 10 MB. La biblioteca (≈ 326 MB) no va en la imagen: se monta o se baja al arrancar.

## 1. Con la biblioteca montada en solo lectura

```bash
M=/Users/Eber/Documents/SideProjects/preguntale-al-peru/biblioteca
docker run -d --name pap-s3-09-prueba -p 127.0.0.1:18000:8000 -e PAP_ANTHROPIC_API_KEY \
  -v $M/dimensiones:/app/biblioteca/dimensiones:ro -v $M/estandarizada:/app/biblioteca/estandarizada:ro \
  -v $M/indicadores:/app/biblioteca/indicadores:ro pap-s3-09:local
```

La clave solo entra por la variable de entorno (`-e` sin valor: se toma del entorno; no se imprime ni está en la imagen).

Registro de arranque: «El cubo coincide con el manifiesto.» y la dirección impresa por `pap servir`.

```text
GET  /salud                  → 200 {"estado": "ok"}      (503 mientras precalienta, ~1 min)
POST /api/preguntar {consulta: q1.json} → 200
  capa 1: «En Huancavelica, la anemia en niñas y niños pequeños no muestra un cambio estadísticamente claro: ni entre 2024
  y 2025 con la forma de medir actual, ni entre 2015 y 2025 con la anterior.»  cifra clave 38,6 %, semáforo verde
docker inspect → Health: healthy
```

## 2. Sin volumen: la imagen baja la biblioteca

`docker run -d -p 127.0.0.1:18001:8000 pap-s3-09:local` (sin montar nada):

```text
No hay biblioteca montada: se baja del release.
Bajando biblioteca-010ea965…   biblioteca-010ea965.tar.zst: OK
Listo: 81 Parquet; cubo 010ea965…
El cubo coincide con el manifiesto.
```

`/salud` → 200 y Q1 → 200. El cubo del release ya coincide con el manifiesto, así que **no se ejercitó** la rama `pap calcular` del arranque (solo corre si no coinciden; usa `--permitir-sucio` porque la imagen no lleva `.git`).

## 3. Nada de crudos ni secretos

- Contexto de build (`.dockerignore`): sin `.git`, `.venv`, `salidas/`, `biblioteca/` (crudos y Parquet), `tests/`, `docs/`, `backlog/`, `odd/`.
- `docker history`: las capas son base, apt (curl, zstd, ca-certificates, uv), usuario, `COPY` de `pyproject/uv.lock/README`, `COPY src`, `uv sync` y `COPY .` (8,57 MB). Ningún `ENV`, `ARG` ni `RUN` contiene una clave; los únicos `ENV` son `UV_*`, `PAP_RAIZ` y `PAP_PUERTO`.
- Dentro de la imagen sin montar nada: `/app` tiene solo `catalogo curados reglas src scripts` y archivos raíz; `biblioteca/` está vacía (sin `cruda/`, sin Parquet); no existen `salidas/` ni `.git`.
- Búsqueda recursiva en `/app` (sin `.venv`) del prefijo de las claves de Anthropic y del nombre de la cabecera de la clave: sin resultados.
- Usuario del proceso: `pap` (uid 1000), no root.

## Limpieza

Contenedores `pap-s3-09-*` eliminados. Se conserva la imagen `pap-s3-09:local` (1,34 GB). El tarball y `/tmp/q1_body.json` solo existieron dentro del contenedor o en `/tmp`.

## Segunda prueba, con la web de S3-04, S3-05 y S3-07 (6/11/2026, orquestador)

La primera prueba se hizo en un worktree aparte, sobre el código anterior a las páginas. Después de integrar S3-07, la imagen se reconstruyó desde el árbol principal (`docker build -t pap-s3-09:local .`) y se levantó con la biblioteca montada en solo lectura:

```
salud 200
inicio 200          (GET /, la página de S3-04)
q1 respuesta 38,6 %
healthy             (HEALTHCHECK de Docker)
1.34GB
pap.web.acceso GET /salud 503 84 ms      (precalentando)
pap.web.acceso GET /salud 200 1 ms
pap.web.acceso GET / 200 7 ms
pap.web.acceso POST /api/preguntar 200 99 ms
```

El registro de acceso de la imagen guarda solo el método, la ruta, el código y el tiempo; la pregunta no aparece (S3-07). El contenedor se borró después de la prueba y la imagen `pap-s3-09:local` quedó para las historias siguientes.

Suite completa en el Mac (6/11/2026): 1161 pasan y 1 falla, `test_imports_permitidos_en_pap_web`. Esa prueba exige que la web importe del motor solo lo permitido, y `servir.py` importaba `pap.motor.plantillas` entero y `pap.web.app`. Se cambió a `from pap.motor.plantillas import textos` y se agregó `pap.web.app: {crear_app}` a la lista. Al repetir `tests/web/test_servicio.py`, `test_servir.py` y `test_sin_secretos.py`, pasan 22 de 22. Total: 1162 pasan y 0 fallan.
