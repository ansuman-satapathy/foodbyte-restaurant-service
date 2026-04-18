FROM python:3.12-alpine3.21 AS builder

RUN apk update && apk upgrade --no-cache && \
    apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine3.21

RUN apk update && apk upgrade --no-cache && \
    addgroup -S app && adduser -S -G app app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY app/ ./app/

USER app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
