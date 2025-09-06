#!/bin/bash

# SSLH Worker Deployment Script
# Usage: ./deploy_worker.sh [local|staging|production] [api_token]

set -e  # Exit on any error
#if token is set then it will not touch this variables
[ -z ${ENVIRONMENT} ] && ENVIRONMENT=${1:-local}
#if token is set then it will not touch this variables
[ -z ${API_TOKEN} ] && API_TOKEN=${2}
#If variable still {} then need an error msg and exit with the error msg
[ -z ${ENVIRONMENT} ] && { echo "Environment Variable not set"; exit 1; }
[ -z ${API_TOKEN} ] && { echo "API_TOKEN Variable not set"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying SSLH Worker for environment: $ENVIRONMENT"

# Validate environment
case $ENVIRONMENT in
    local|staging|production)
        echo "✅ Valid environment: $ENVIRONMENT"
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "Usage: $0 [local|staging|production] [api_token]"
        exit 1
        ;;
esac

# Set configuration file path
CONFIG_FILE="$PROJECT_ROOT/config/worker_${ENVIRONMENT}.json"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

echo "📋 Using configuration: $CONFIG_FILE"

# Handle API token
if [[ -n "$API_TOKEN" ]]; then
    echo "🔑 API token provided via command line"
    # Create temporary config with API token substituted
    TEMP_CONFIG="/tmp/sslh_worker_${ENVIRONMENT}_$(date +%s).json"
    sed "s/\${SSLH_API_TOKEN}/$API_TOKEN/g; s/\${SSLH_STAGING_TOKEN}/$API_TOKEN/g" "$CONFIG_FILE" > "$TEMP_CONFIG"
    CONFIG_FILE="$TEMP_CONFIG"
elif [[ "$ENVIRONMENT" == "production" && -z "$SSLH_API_TOKEN" ]]; then
    echo "❌ Production deployment requires API token"
    echo "Either set SSLH_API_TOKEN environment variable or pass as argument"
    exit 1
elif [[ "$ENVIRONMENT" == "staging" && -z "$SSLH_STAGING_TOKEN" ]]; then
    echo "❌ Staging deployment requires API token"
    echo "Either set SSLH_STAGING_TOKEN environment variable or pass as argument"
    exit 1
fi

# Validate Python dependencies
echo "🔍 Checking Python dependencies..."
if ! python3 -c "import requests, json" 2>/dev/null; then
    echo "❌ Missing Python dependencies. Installing..."
    pip3 install requests
fi

# Create necessary directories
echo "📁 Creating workspace directories..."
LOCAL_DIR=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['LOCAL'])")
NAS_DIR=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['NAS'])")

mkdir -p "$LOCAL_DIR" 2>/dev/null || echo "ℹ️  Local directory already exists or cannot create: $LOCAL_DIR"
mkdir -p "$NAS_DIR" 2>/dev/null || echo "ℹ️  NAS directory already exists or cannot create: $NAS_DIR"

# Test connection to server
echo "🌐 Testing connection to server..."
SERVER_URL=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config['SERVER'])")
if curl -s --connect-timeout 10 "$SERVER_URL" >/dev/null 2>&1; then
    echo "✅ Server is reachable: $SERVER_URL"
else
    echo "⚠️  Warning: Could not reach server: $SERVER_URL"
    echo "   This might be normal if server is not running or firewall is blocking"
fi

# Start the worker
echo "🔄 Starting SSLH Worker..."
echo "   Environment: $ENVIRONMENT"
echo "   Config: $CONFIG_FILE"
echo "   Press Ctrl+C to stop"
echo ""

cd "$PROJECT_ROOT"
python3 sslh-dummy-worker.py -c "$CONFIG_FILE"

# Cleanup temporary files
if [[ -f "$TEMP_CONFIG" ]]; then
    rm -f "$TEMP_CONFIG"
fi

echo "👋 Worker stopped"
