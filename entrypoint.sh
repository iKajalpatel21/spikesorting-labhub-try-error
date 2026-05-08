#!/bin/bash
set -e

# Run database migrations automatically on every container start.
# Safe to run repeatedly — Django skips already-applied migrations.
python manage.py migrate --noinput

# Hand off to the main process (Gunicorn).
exec "$@"
