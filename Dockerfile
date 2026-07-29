# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

# Keep Python lean and predictable in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

# System packages needed at runtime by Pillow / cryptography wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copy the project
COPY . /code

# The logging config writes to these files at import time, so the dir must exist.
RUN mkdir -p /code/logs

# Collect static files into STATIC_ROOT for WhiteNoise to serve.
# A throwaway SECRET_KEY satisfies settings import; the real one is a Fly secret.
RUN SECRET_KEY=build-only-not-a-secret DEBUG=False python manage.py collectstatic --noinput

EXPOSE 8000

# entrypoint runs migrations (on the mounted volume) then starts the ASGI server
RUN chmod +x /code/entrypoint.sh
CMD ["/code/entrypoint.sh"]
