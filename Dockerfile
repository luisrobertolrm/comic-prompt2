# ── Stage 1: Angular build ────────────────────────────────────────────────────
FROM node:22-alpine AS frontend
WORKDIR /app
COPY sumi-web/package*.json ./
RUN npm ci
COPY sumi-web/ .
RUN npm run build

# ── Stage 2: Python API ───────────────────────────────────────────────────────
FROM python:3.13-slim
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Instala dependências Python (layer cacheada — só roda de novo se pyproject/uv.lock mudarem)
COPY sumi-api/pyproject.toml sumi-api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copia código-fonte
COPY sumi-api/src ./src
COPY sumi-api/models ./models
COPY sumi-api/alembic ./alembic
COPY sumi-api/alembic.ini ./

# Copia build do Angular
COPY --from=frontend /app/dist/sumi-web/browser ./static/app

RUN mkdir -p static/images

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src
ENV APP_ENV=production
ENV APP_RELOAD=false

EXPOSE 8000

# ${PORT} é injetado pelo Railway; fallback 8000 para testes locais
CMD ["sh", "-c", "uvicorn prompt_clinica.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
