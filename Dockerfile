FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# A coleta nao precisa acessar o banco e gera os arquivos que o Apache servira.
RUN SECRET_KEY=build-temporario DEBUG=False STATIC_ROOT=/app/staticfiles \
    python manage.py collectstatic --noinput --settings=config.settings.prod

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
