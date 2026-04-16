# ── Build stage ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Update packages to fix potential CVEs
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends gcc libc6-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ────────────────────────────────────────────────────────
FROM python:3.13-slim

# Update packages and create non-root user
RUN apt-get update && apt-get upgrade -y && \
    addgroup --system app && adduser --system --group app && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app
COPY app/ ./app/

USER app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
