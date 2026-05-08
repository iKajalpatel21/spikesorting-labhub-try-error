#!/bin/bash
set -e

# Collect static files — needs DJANGO_SECRET_KEY from the environment,
# so must run here rather than at image build time.
python manage.py collectstatic --noinput

# Run database migrations — safe to run repeatedly.
python manage.py migrate --noinput

# Hand off to the main process (Gunicorn).
exec "$@"
