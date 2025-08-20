#!/bin/bash

# Simple QModel Deployment Script
# Similar to your sample but enhanced for qmodel requirements

set -e  # Exit on any error

# Create environment and activate it
[ -d .djangovenv ] || python3 -m venv .djangovenv
source .djangovenv/bin/activate || exit 1

# Update or install all packages
pip install -U pip || exit 1

# Install from requirements.txt if available, otherwise core packages
if [ -f requirements.txt ]; then
    pip install -U -r requirements.txt || exit 1
else
    pip install -U django djangorestframework requests gunicorn urllib3 || exit 1
fi

# Brutally clear db (optional - ask user)
read -p "Reset database? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -n > db.sqlite3
fi

# Init db
python manage.py makemigrations || exit 1
python manage.py migrate || exit 1

# Create superuser
echo "Creating superuser (admin)..."
python manage.py createsuperuser --username admin || exit 1

# Generate SSL certificates if not present
if [ ! -f cert.pem ] || [ ! -f key.pem ]; then
    echo "Generating SSL certificates..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/C=US/ST=CA/L=San Francisco/O=Development/CN=localhost" || exit 1
fi

# Collect static files
yes yes | python manage.py collectstatic || exit 1

# Ask how to run server
echo "How would you like to run the server?"
echo "1) Development server (python manage.py runserver)"
echo "2) Gunicorn HTTP (port 8000)" 
echo "3) Gunicorn HTTPS (port 8443)"
read -p "Choose (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        python manage.py runserver || exit 1
        ;;
    2)
        gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application || exit 1
        ;;
    3)
        gunicorn --bind 127.0.0.1:8443 --certfile=cert.pem --keyfile=key.pem labhub.wsgi:application || exit 1
        ;;
    *)
        echo "Invalid choice. Run manually:"
        echo "  python manage.py runserver"
        echo "  OR"
        echo "  gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application"
        ;;
esac
