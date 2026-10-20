FROM python:3.14.7-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=book_shop.settings.production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    libpq-dev \
    python3-dev \
    pkg-config \
    pgloader \
    gcc \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the whole project (the .dockerignore keeps .env, .venv, caches out).
COPY . .

# Collect static files into /app/staticfiles at build time so WhiteNoise can
# serve them. The values below are throw-away placeholders only to satisfy the
# production settings' fail-fast checks; they are NOT baked into the runtime
# environment (they apply to this single RUN).
RUN DJANGO_SECRET_KEY=build-only-not-a-secret \
    DJANGO_ALLOWED_HOSTS=build.invalid \
    CSRF_TRUSTED_ORIGINS=https://build.invalid \
    EMAIL_HOST_USER=build EMAIL_HOST_PASSWORD=build \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Liveness only (no DB/Redis): the X-Forwarded-Proto header and the Host header
# mimic nginx so the request is accepted over plain HTTP.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen(u.Request('http://localhost:8000/health/', headers={'X-Forwarded-Proto': 'https'}))"

CMD ["gunicorn", "book_shop.asgi:application", "-c", "gunicorn.conf.py"]
