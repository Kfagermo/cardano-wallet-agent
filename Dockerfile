FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (include build tools for ARM/Raspberry Pi compatibility)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src ./src
COPY templates ./templates
COPY README.md SURVIVAL_PLAN.md DEPLOYMENT.md ./

# Runtime dirs (mounted as volumes in prod if you want persistence)
RUN mkdir -p reports data

EXPOSE 8000
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
