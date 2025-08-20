#!/bin/bash

# =============================================================================
# QModel Django Deployment Script
# =============================================================================
# This script sets up the complete environment for the qmodel branch including:
# - GitHub repository setup
# - Virtual environment creation
# - Dependencies installation
# - Database initialization
# - SSL certificate generation
# - Static files collection
# - Server startup options
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/iKajalpatel21/spikesorting-labhub-try-error.git"
BRANCH_NAME="qmodel"
PROJECT_DIR="spikesorting-labhub-try-error"
VENV_NAME=".djangovenv"

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# 1. System Requirements Check
# =============================================================================
print_status "Checking system requirements..."

if ! command_exists python3; then
    print_error "Python3 is not installed. Please install Python3 first."
    exit 1
fi

if ! command_exists git; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

if ! command_exists openssl; then
    print_error "OpenSSL is not installed. Please install OpenSSL first."
    exit 1
fi

print_success "All system requirements are met."

# =============================================================================
# 2. Repository Setup
# =============================================================================
print_status "Setting up repository..."

# Check if we're already in the project directory
if [[ $(basename "$PWD") == "$PROJECT_DIR" ]]; then
    print_status "Already in project directory. Pulling latest changes..."
    git fetch origin
    git checkout $BRANCH_NAME || git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
    git pull origin $BRANCH_NAME
else
    # Check if project directory exists
    if [ -d "$PROJECT_DIR" ]; then
        print_status "Project directory exists. Updating..."
        cd "$PROJECT_DIR"
        git fetch origin
        git checkout $BRANCH_NAME || git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
        git pull origin $BRANCH_NAME
    else
        print_status "Cloning repository..."
        git clone -b $BRANCH_NAME $REPO_URL $PROJECT_DIR
        cd "$PROJECT_DIR"
    fi
fi

print_success "Repository setup complete."

# =============================================================================
# 3. Virtual Environment Setup
# =============================================================================
print_status "Setting up Python virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    python3 -m venv $VENV_NAME || {
        print_error "Failed to create virtual environment"
        exit 1
    }
fi

# Activate virtual environment
source $VENV_NAME/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

print_success "Virtual environment activated."

# =============================================================================
# 4. Dependencies Installation
# =============================================================================
print_status "Installing/updating dependencies..."

# Update pip
pip install -U pip || {
    print_error "Failed to update pip"
    exit 1
}

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -U -r requirements.txt || {
        print_error "Failed to install requirements from requirements.txt"
        exit 1
    }
else
    # Fallback to manual installation
    print_warning "requirements.txt not found. Installing core dependencies manually..."
    pip install -U django djangorestframework requests gunicorn urllib3 || {
        print_error "Failed to install core dependencies"
        exit 1
    }
fi

print_success "Dependencies installed successfully."

# =============================================================================
# 5. Database Setup
# =============================================================================
print_status "Setting up database..."

# Ask user if they want to reset the database
read -p "Do you want to reset the database? This will clear all existing data. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Resetting database..."
    echo -n > db.sqlite3
fi

# Run migrations
print_status "Running database migrations..."
python manage.py makemigrations || {
    print_error "Failed to create migrations"
    exit 1
}

python manage.py migrate || {
    print_error "Failed to run migrations"
    exit 1
}

print_success "Database setup complete."

# =============================================================================
# 6. Create Superuser (Optional)
# =============================================================================
read -p "Do you want to create a superuser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Creating superuser..."
    python manage.py createsuperuser --username admin || {
        print_warning "Superuser creation failed or was skipped"
    }
fi

# =============================================================================
# 7. SSL Certificate Generation
# =============================================================================
print_status "Checking SSL certificates..."

if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    print_status "Generating SSL certificates for HTTPS..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/C=US/ST=CA/L=San Francisco/O=Development/CN=localhost" || {
        print_error "Failed to generate SSL certificates"
        exit 1
    }
    print_success "SSL certificates generated."
else
    print_success "SSL certificates already exist."
fi

# =============================================================================
# 8. Static Files Collection
# =============================================================================
print_status "Collecting static files..."
yes yes | python manage.py collectstatic || {
    print_warning "Static files collection failed or was skipped"
}

print_success "Static files collected."

# =============================================================================
# 9. Server Startup Options
# =============================================================================
print_success "Deployment complete! Choose how to run the server:"
echo
echo "Available options:"
echo "1) Development server (HTTP on port 8000)"
echo "2) Gunicorn server (HTTP on port 8000)"
echo "3) Gunicorn server with HTTPS (port 8443)"
echo "4) Just setup - don't start server"
echo "5) Start worker only"
echo

read -p "Enter your choice (1-5): " -n 1 -r
echo

case $REPLY in
    1)
        print_status "Starting Django development server..."
        python manage.py runserver
        ;;
    2)
        print_status "Starting Gunicorn HTTP server..."
        gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application
        ;;
    3)
        print_status "Starting Gunicorn HTTPS server..."
        gunicorn --bind 127.0.0.1:8443 \
                 --certfile=cert.pem \
                 --keyfile=key.pem \
                 labhub.wsgi:application
        ;;
    4)
        print_success "Setup complete. You can manually start the server when ready."
        echo
        echo "To start the development server: python manage.py runserver"
        echo "To start Gunicorn HTTP: gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application"
        echo "To start Gunicorn HTTPS: gunicorn --bind 127.0.0.1:8443 --certfile=cert.pem --keyfile=key.pem labhub.wsgi:application"
        echo "To start worker: python qmodel_worker.py"
        ;;
    5)
        print_status "Starting qmodel worker..."
        python qmodel_worker.py
        ;;
    *)
        print_warning "Invalid choice. Setup complete but no server started."
        ;;
esac

# =============================================================================
# 10. Final Instructions
# =============================================================================
echo
print_success "=== Deployment Summary ==="
echo "Project: $PROJECT_DIR"
echo "Branch: $BRANCH_NAME"
echo "Virtual Environment: $VENV_NAME"
echo "Database: SQLite (db.sqlite3)"
echo "SSL Certificates: cert.pem, key.pem"
echo
echo "=== Usage Instructions ==="
echo "• Access Django admin: http://localhost:8000/admin/ (or https://localhost:8443/admin/)"
echo "• Submit jobs: http://localhost:8000/qmodel/submit/ (or https://localhost:8443/qmodel/submit/)"
echo "• API endpoint: http://localhost:8000/qmodel/getthenextjob/ (or https://localhost:8443/qmodel/getthenextjob/)"
echo "• Worker script: python qmodel_worker.py"
echo
echo "=== Multiple Terminal Setup ==="
echo "Terminal 1 (Server): ./deploy.sh (choose option 2 or 3)"
echo "Terminal 2 (Worker): source $VENV_NAME/bin/activate && python qmodel_worker.py"
echo
print_success "Setup complete! Enjoy your deployment and run the server as needed."
