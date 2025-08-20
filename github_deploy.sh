#!/bin/bash

# GitHub Branch Deployment Script for QModel
# Clones/updates from GitHub qmodel branch and sets up environment

set -e  # Exit on any error

# Configuration
REPO_URL="https://github.com/iKajalpatel21/spikesorting-labhub-try-error.git"
BRANCH_NAME="qmodel"
PROJECT_DIR="spikesorting-labhub-try-error"

echo "🚀 QModel GitHub Branch Deployment"
echo "=================================="

# Check if we're in project directory or need to clone
if [[ $(basename "$PWD") == "$PROJECT_DIR" ]]; then
    echo "📁 Already in project directory. Updating from GitHub..."
    git fetch origin
    git checkout $BRANCH_NAME || git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
    git pull origin $BRANCH_NAME
elif [ -d "$PROJECT_DIR" ]; then
    echo "📁 Project directory exists. Updating..."
    cd "$PROJECT_DIR"
    git fetch origin
    git checkout $BRANCH_NAME || git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
    git pull origin $BRANCH_NAME
else
    echo "📥 Cloning repository from GitHub..."
    git clone -b $BRANCH_NAME $REPO_URL $PROJECT_DIR
    cd "$PROJECT_DIR"
fi

echo "✅ Repository updated from GitHub qmodel branch"

# Create environment and activate it
echo "🐍 Setting up Python environment..."
[ -d .djangovenv ] || python3 -m venv .djangovenv
source .djangovenv/bin/activate || exit 1

# Update or install all packages
echo "📦 Installing dependencies..."
pip install -U pip || exit 1
pip install -U -r requirements.txt || exit 1

# Ask about database reset
read -p "🗄️  Reset database? This will clear all data (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Clearing database..."
    echo -n > db.sqlite3
fi

# Init db
echo "🏗️  Setting up database..."
python manage.py makemigrations || exit 1
python manage.py migrate || exit 1

# Create superuser
echo "👤 Creating superuser..."
python manage.py createsuperuser --username admin || exit 1

# Generate SSL certificates if needed
if [ ! -f cert.pem ] || [ ! -f key.pem ]; then
    echo "🔐 Generating SSL certificates..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/C=US/ST=CA/L=San Francisco/O=Development/CN=localhost" || exit 1
fi

# Collect static files
echo "📁 Collecting static files..."
yes yes | python manage.py collectstatic || exit 1

echo ""
echo "🎉 Deployment from GitHub complete!"
echo ""
echo "🚀 Ready to run:"
echo "   For HTTPS Gunicorn: gunicorn --bind 127.0.0.1:8443 --certfile=cert.pem --keyfile=key.pem labhub.wsgi:application"
echo "   For HTTP Gunicorn:  gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application"
echo "   For Development:    python manage.py runserver"
echo "   For Worker:         python qmodel_worker.py"
echo ""
echo "🌐 Access URLs:"
echo "   Django Admin: https://localhost:8443/admin/"
echo "   Job Submit:   https://localhost:8443/qmodel/submit/"
echo "   API Endpoint: https://localhost:8443/qmodel/getthenextjob/"
