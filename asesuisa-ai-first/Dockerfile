# Imagen única: compila la UI y la sirve desde el backend (FastAPI).
# NOTA: este Dockerfile no pudo construirse en el entorno de desarrollo (sin demonio de Docker);
# se valida en CI. Ver docs/ARCHITECTURE.md.
FROM node:22-slim AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN useradd --create-home --uid 10001 app
WORKDIR /srv
COPY backend/requirements.txt backend/requirements-postgres.txt ./backend/
RUN pip install -r backend/requirements.txt -r backend/requirements-postgres.txt
COPY backend/ ./backend/
COPY --from=ui /ui/dist ./frontend/dist
USER app
WORKDIR /srv/backend
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
