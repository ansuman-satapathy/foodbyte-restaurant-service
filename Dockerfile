# ── Build stage ──────────────────────────────────────────────────────────
FROM python:3.13-alpine AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ────────────────────────────────────────────────────────
FROM python:3.13-alpine

RUN addgroup -S app && adduser -S -G app app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY app/ ./app/

USER app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
