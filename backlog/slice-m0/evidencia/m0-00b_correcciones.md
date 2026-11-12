# M0-00b — Correcciones A1–A9 (diff por cada una)

9/11/2026. Los diffs están resumidos; el completo es `git diff` de la rama `slice-m0`.

## A1, A2, A4 — `pyproject.toml` y `uv.lock`
```diff
-    "python-multipart>=0.0.33",
+    "python-multipart>=0.0.32",
@@ dev
+    "pytest-socket>=0.8.1",          # nueva dependencia de desarrollo, con auditoría
+[tool.uv]
+exclude-newer = "2 weeks"
+constraint-dependencies = ["pillow>=13.0.0", "certifi>=2026.10.18"]
```
`uv lock`: `certifi` 2026.7.22 → 2026.10.23, `pillow` 12.3.0 → 13.0.0, `python-multipart` 0.0.33 → 0.0.32, `opentelemetry-api` 1.45.2 → 1.45.1, más `pytest-socket` 0.8.1 (nuevo). Comprobación: `scripts/auditar.sh` en verde y `tests/test_lock_seguro.py`.

## A3 — `src/pap/capa0/encuestas.py`, `src/pap/capa0/insumos.py` (+ `src/pap/zip_seguro.py`, ya hecho)
```diff
-    with zipfile.ZipFile(ins.ruta) as z:
-        nombres = [n for n in z.namelist() if re.search(patron, n.rsplit("/", 1)[-1], re.I)]
+    with abrir_zip_seguro(ins.ruta) as z:
+        nombres = [n for n in z.miembros() if re.search(patron, n.rsplit("/", 1)[-1], re.I)]
-            t.write(z.read(miembro))
+            z.copiar(miembro, t)                       # en flujo, por bloques
 # insumos.py
-    with zipfile.ZipFile(insumo.ruta) as z:   ... z.read(nombres[0])
+    with abrir_zip_seguro(insumo.ruta) as z:  ... z.leer(nombres[0])
-        return [(n, z.read(n)) for n in sorted(z.namelist()) if ... and not n.endswith("/")]
+        return [(n, z.leer(n)) for n in sorted(z.miembros()) if ...]     # `miembros()` ya excluye los directorios
```
Límites en `curados/inferencia/parametros.yaml` (`supuesto: M0-00b`). Pruebas: `tests/test_zip_seguro.py` (12) y las que leen ZIP reales (`test_s4_insumos`, `test_sien`, `test_puentes`, `test_calculo_p1`, `test_piloto_indicadores`).

## A5 — `.gitignore`
```diff
+# Secretos locales (M0-00b, A5)
+.env
+.env.*
```

## A6 — `Dockerfile`
```diff
-FROM python:3.12-slim
+FROM python:3.12.16-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
+COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /usr/local/bin/
-    && rm -rf /var/lib/apt/lists/* \
-    && pip install --no-cache-dir uv==0.13.7
+    && rm -rf /var/lib/apt/lists/*
-RUN uv sync --frozen --no-dev --no-cache
+RUN uv sync --locked --no-build --no-dev --no-cache
```
`uv` 0.13.5 y no 0.13.7: la 0.13.7 tenía menos de 2 semanas el 9/11/2026. Las huellas son las del índice multi-arquitectura (consultadas en Docker Hub y ghcr.io). **La imagen no se pudo construir en esta corrida: el demonio de Docker no estaba corriendo** (el cliente existe, v29.9.3). El criterio «se construye y `/salud` responde» queda **pendiente**; se verifica en el Mac con Docker abierto: `docker build -t pap-m0:local . && docker run --rm -p 8000:8000 pap-m0:local`.

## A7 — `.python-version`
```diff
-3.12
+3.12.16
```

## A8 — `curados/releases.yaml` (nuevo) y `scripts/bajar_biblioteca.sh`
- `curados/releases.yaml` guarda `sha256: 4c10cad0…a904` de `biblioteca-010ea965.tar.zst`. Se copió del `SHA256SUMS` del release y **se recalculó con `shasum -a 256` sobre el paquete bajado (314 226 406 bytes): coincide**.
```diff
-curl … SHA256SUMS ; curl … .tar.zst ; (cd "$TMP" && sha256sum -c SHA256SUMS)
+ESPERADA_PAQUETE=<huella leída de curados/releases.yaml; si no hay, error y no se baja nada>
+curl … .tar.zst ; REAL_PAQUETE=$(sha256sum …) ; si difiere de ESPERADA_PAQUETE → error
```
Pruebas: `tests/test_bajar_biblioteca.py` (3, sin red). El script completo no se corrió de punta a punta para no sobrescribir la biblioteca local (314 MB).

## A9 — `tests/test_sin_secretos.py`
```diff
+TOKENS_GITHUB = re.compile(rb"(?:gh" + b"p_|github_" + b"pat_|gh" + b"o_)[A-Za-z0-9_]{20,}")   # armado por partes
+    tokens = [... for p in archivos if TOKENS_GITHUB.search(p.read_bytes())]
+def test_el_detector_de_tokens_de_github_los_encuentra_y_no_confunde_la_documentacion(): ...
```
Busca el prefijo con su cuerpo (≥ 20 caracteres) porque la historia nombra los prefijos en prosa (supuesto en `consultas_al_dueno.md`).

## Controles de la tarea 6 (archivos nuevos)
`scripts/auditar.sh` + `just auditar`/`just secretos` (C3), `tests/test_lock_seguro.py` (C2), `pytest-socket` en `addopts` + `HF_HUB_OFFLINE`/`SVYLAB_OFFLINE` en `tests/conftest.py` (C5), `tests/test_apis_prohibidas.py` (C6), `scripts/ganchos/pre-commit` + `scripts/instalar_ganchos.sh` (C9).
