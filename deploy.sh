#!/bin/bash

# =============================================================================
# Spike Sorting Lab Hub — Docker Deployment Helper
# =============================================================================
# This script intentionally does not clone the repo, create a Python virtualenv,
# install Django locally, or run local manage.py commands.
#
# Django and project dependencies are installed by the Dockerfile during
# `docker compose build`. Runtime state lives in bind-mounted directories.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="spikesorting-labhub"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

compose() {
    docker compose "$@"
}

# =============================================================================
# 1. Docker Requirements
# =============================================================================
print_status "Checking Docker deployment requirements..."

if ! command_exists docker; then
    print_error "Docker is not installed or is not on PATH."
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose v2 is not available. Install Docker Compose before deploying."
    exit 1
fi

if ! command_exists openssl; then
    print_error "OpenSSL is required to generate local TLS certificates."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml was not found. Run this script from the project root."
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile was not found. Run this script from the project root."
    exit 1
fi

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
    print_warning "DJANGO_SECRET_KEY is not set. Set it before production deployment."
fi

print_success "Docker requirements look good."

# =============================================================================
# 2. SSL Certificates
# =============================================================================
print_status "Checking SSL certificates..."

mkdir -p secrets
if [ ! -f "secrets/cert.crt" ] || [ ! -f "secrets/cert.key" ]; then
    print_status "Generating self-signed SSL certificate in secrets/..."
    SERVER_HOST=$(hostname -f 2>/dev/null || hostname)
    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="127.0.0.1"
    fi

    openssl req -x509 -newkey rsa:4096 \
        -keyout secrets/cert.key \
        -out secrets/cert.crt \
        -days 365 \
        -nodes \
        -subj "/CN=${SERVER_HOST}" \
        -addext "subjectAltName=DNS:${SERVER_HOST},IP:${SERVER_IP},DNS:localhost,IP:127.0.0.1"

    print_success "SSL certificate generated at secrets/cert.crt and secrets/cert.key."
else
    print_success "SSL certificates already exist."
fi

# =============================================================================
# 3. Docker Deployment Actions
# =============================================================================
echo
print_success "Docker deployment helper is ready."
echo
echo "Choose an action:"
echo "1) Build image"
echo "2) Start containers"
echo "3) Build and start containers"
echo "4) Run migrations inside container"
echo "5) Create superuser inside container"
echo "6) Show logs"
echo "7) Stop containers"
echo "8) Exit"
echo

read -p "Enter your choice (1-8): " -n 1 -r
echo

case $REPLY in
    1)
        print_status "Building Docker image..."
        compose build
        print_success "Image build complete."
        ;;
    2)
        print_status "Starting containers..."
        compose up -d
        print_success "Containers started."
        ;;
    3)
        print_status "Building image and starting containers..."
        compose up -d --build
        print_success "Containers built and started."
        ;;
    4)
        print_status "Running migrations inside the container..."
        compose exec "$SERVICE_NAME" python manage.py migrate
        print_success "Migrations complete."
        ;;
    5)
        print_status "Creating a superuser inside the running container..."
        compose exec "$SERVICE_NAME" python manage.py createsuperuser
        ;;
    6)
        print_status "Showing container logs..."
        compose logs -f "$SERVICE_NAME"
        ;;
    7)
        print_status "Stopping containers..."
        compose down
        print_success "Containers stopped."
        ;;
    8)
        print_success "No action taken."
        ;;
    *)
        print_warning "Invalid choice. No action taken."
        ;;
esac

echo
print_success "=== Docker Deployment Summary ==="
echo "App service: $SERVICE_NAME"
echo "Django app path in container: /app"
echo "Django database path in container: /django_db/db.sqlite3"
echo "NAS data path in container: /data"
echo "Experiment files path in container: /experiments"
echo "HTTP:  http://localhost:9000/"
echo "HTTPS: https://localhost:9443/"
echo
echo "Common commands:"
echo "  docker compose up -d --build"
echo "  docker compose exec $SERVICE_NAME python manage.py migrate"
echo "  docker compose exec $SERVICE_NAME python manage.py createsuperuser"
echo "  docker compose logs -f $SERVICE_NAME"
