#!/bin/bash
# =============================================================================
# Spike Sorting Lab Hub — Host pre-flight helper
#
# Run this before `docker compose up` to make sure the host environment
# is ready.  Does NOT start, stop, or manage containers.
#
#   1. Check the external database directory exists (warn if missing).
#   2. Check SSL certificates — create if absent, leave untouched if present.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# 1. Database directory
# =============================================================================
DB_DIR="/mnt/root_data_storage/users/sslh/persistentdata"

if [ -d "$DB_DIR" ]; then
    ok "Database directory exists: $DB_DIR"
else
    warn "Database directory not found: $DB_DIR"
    warn "The container will start but /django_db will be empty — run migrations after mounting."
fi

# =============================================================================
# 2. SSL Certificates
# =============================================================================
mkdir -p secrets

if [ -f "secrets/cert.crt" ] && [ -f "secrets/cert.key" ]; then
    ok "SSL certificates already exist — leaving untouched."
else
    echo "Generating self-signed TLS certificate into secrets/..."

    SERVER_HOST=$(hostname -f 2>/dev/null || hostname)
    SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -z "$SERVER_IP" ] && SERVER_IP="127.0.0.1"

    openssl req -x509 -newkey rsa:4096 \
        -keyout secrets/cert.key \
        -out    secrets/cert.crt \
        -days   365 -nodes \
        -subj   "/CN=${SERVER_HOST}" \
        -addext "subjectAltName=DNS:${SERVER_HOST},IP:${SERVER_IP},DNS:localhost,IP:127.0.0.1"

    ok "Certificate created: secrets/cert.crt (CN=${SERVER_HOST}, IP=${SERVER_IP})"
fi
