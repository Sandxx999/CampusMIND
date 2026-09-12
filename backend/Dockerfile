# Production-grade multi-stage Dockerfile for CampusMIND 2.0 Backend
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and pre-build wheels
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runner Stage
FROM python:3.11-slim AS runner

WORKDIR /app

# Security: Create non-root user
RUN groupadd -r campusmind && useradd -r -g campusmind appuser

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/data/hf_cache
ENV CHROMA_DB_DIR=/app/data/chroma_db
ENV DATABASE_URL=sqlite:////app/data/campusmind.db

# Copy backend application source
COPY backend/ .

# Copy raw data files so they are available at /data/raw
COPY data/ /data/

# Adjust permissions for non-root execution
RUN chown -R appuser:campusmind /app && chown -R appuser:campusmind /data

USER appuser

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
