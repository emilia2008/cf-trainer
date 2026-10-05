FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Run as an unprivileged user. It owns /app so the SQLite fallback (no DATABASE_URL) can create
# its file; production sets DATABASE_URL to PostgreSQL.
RUN useradd --create-home --uid 1000 appuser && chown appuser:appuser /app
USER appuser

EXPOSE 8000
# Hosting platforms (Render, Railway, Koyeb, ...) pass the port in $PORT; default to 8000.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
