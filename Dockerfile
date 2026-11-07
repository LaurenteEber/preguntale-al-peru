# S3-09 — Imagen de Pregúntale al Perú (P-05: solo local; sin despliegue público, eso es del slice 4).
#   docker build -t pap-s3-09:local .
#   docker run --rm -p 8000:8000 -e PAP_ANTHROPIC_API_KEY pap-s3-09:local     # la clave solo por variable de entorno
# Con la biblioteca ya bajada se monta en solo lectura (dimensiones, estandarizada, indicadores en /app/biblioteca/…);
# sin ella, el arranque la baja del release (scripts/bajar_biblioteca.sh).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl zstd ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv==0.13.7

RUN useradd --create-home --uid 1000 pap
WORKDIR /app
RUN chown pap:pap /app
USER pap

ENV UV_PYTHON_DOWNLOADS=never UV_PYTHON_PREFERENCE=only-system UV_LINK_MODE=copy PAP_RAIZ=/app PAP_PUERTO=8000

COPY --chown=pap:pap pyproject.toml uv.lock README.md ./
COPY --chown=pap:pap src ./src
RUN uv sync --frozen --no-dev --no-cache
COPY --chown=pap:pap . .
RUN mkdir -p biblioteca

EXPOSE 8000
# El precalentamiento tarda: /salud responde 503 hasta que termina, por eso el periodo de gracia.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PAP_PUERTO', '8000') + '/salud')"

ENTRYPOINT ["scripts/arranque_imagen.sh"]
