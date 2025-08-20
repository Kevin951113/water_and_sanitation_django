# ---- Base image ----
FROM python:3.12-slim

# Python defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for mysqlclient (Debian slim) + curl (optional for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
  && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install gunicorn mysqlclient
# ^ If gunicorn/mysqlclient are already in requirements.txt, remove the last line.

# ---- App code ----
COPY . /app

# ---- Non-root user ----
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

# ---- Runtime env ----
ENV PORT=8000 \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4
EXPOSE 8000

# (Optional) HEALTHCHECK — comment out if you don’t have a /healthz route
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/healthz || exit 1

# Start-up flow:
# 1) migrate
# 2) optionally collectstatic when COLLECT_STATIC=1 and STATIC_ROOT is set in settings.py
# 3) run gunicorn
CMD ["/bin/sh","-lc","\
  python manage.py migrate --noinput && \
  if [ \"${COLLECT_STATIC:-0}\" = \"1\" ]; then python manage.py collectstatic --noinput; fi && \
  gunicorn config.wsgi:application \
    -b 0.0.0.0:${PORT} \
    -w ${GUNICORN_WORKERS} \
    -k gthread --threads ${GUNICORN_THREADS} \
    --timeout 60 \
    --access-logfile - --error-logfile - \
"]
