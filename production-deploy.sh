#!/bin/bash

# =============================================================================
# SSLH LabHub Production Deployment Script
# =============================================================================
# This script sets up the complete environment for the clean-configuration-system branch including:
# - GitHub repository setup
# - Virtual environment creation
# - Dependencies installation
# - Database initialization with superuser
# - SSL certificate generation
# - Static files collection
# - Production Gunicorn HTTPS server
# - Worker configuration and startup
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
BRANCH_NAME="clean-configuration-system"
PROJECT_DIR="spikesorting-labhub-try-error"
VENV_NAME=".venv"

# Server configuration
DEFAULT_HTTP_PORT=8000
DEFAULT_HTTPS_PORT=8443
DEFAULT_WORKERS=2

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

# Generate random token
generate_token() {
    python3 -c "import secrets; print(secrets.token_hex(20))"
}

# =============================================================================
# 1. System Requirements Check
# =============================================================================
check_requirements() {
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

    # Check Python version
    PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $PYTHON_VER"

    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8+ is required. Current version: $PYTHON_VER"
        exit 1
    fi

    print_success "All system requirements are met."
}

# =============================================================================
# 2. Repository Setup
# =============================================================================
setup_repository() {
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

    print_success "Repository setup complete on branch: $BRANCH_NAME"
}

# =============================================================================
# 3. Virtual Environment Setup
# =============================================================================
setup_virtual_environment() {
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

    print_success "Virtual environment activated: $VENV_NAME"
}

# =============================================================================
# 4. Dependencies Installation
# =============================================================================
install_dependencies() {
    print_status "Installing/updating dependencies..."

    # Update pip
    pip install --upgrade pip || {
        print_error "Failed to update pip"
        exit 1
    }

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt || {
            print_error "Failed to install requirements from requirements.txt"
            exit 1
        }
    else
        print_error "requirements.txt not found!"
        exit 1
    fi

    print_success "Dependencies installed successfully."
}

# =============================================================================
# 5. Environment Configuration
# =============================================================================
setup_environment_variables() {
    print_status "Setting up environment variables..."

    # Generate API token if not set
    if [ -z "$SSLH_API_TOKEN" ]; then
        export SSLH_API_TOKEN=$(generate_token)
        print_success "Generated API token: $SSLH_API_TOKEN"
        print_warning "IMPORTANT: Save this token for worker configuration!"
    fi

    # Set Django settings
    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-labhub.settings}"
    
    # Generate secret key if not set
    if [ -z "$DJANGO_SECRET_KEY" ]; then
        export DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    fi

    # Set superuser credentials
    export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
    export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@localhost}"
    export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin}"

    print_success "Environment variables configured."
}

# =============================================================================
# 6. Update Production Configuration
# =============================================================================
update_production_config() {
    print_status "Updating production configuration..."

    # Create production config from template if it doesn't exist
    if [ ! -f "config/worker_production.json" ]; then
        print_status "Creating production worker configuration..."
        mkdir -p config
        cat > config/worker_production.json << EOF
{
    "SERVER": "https://127.0.0.1:8443/qmodel",
    "SSH_KEY": "",
    "NAS": "/tmp/sslh-worker-data",
    "LOCAL": "/tmp/sslh-workspace",
    "TIMEOUT": 30,
    "API_TOKEN": "$SSLH_API_TOKEN",
    "VERIFY_SSL": false,
    "JOB_SAVE": true
}
EOF
    else
        # Update existing config with actual token
        if grep -q "\${SSLH_API_TOKEN}" config/worker_production.json; then
            sed -i.backup "s/\${SSLH_API_TOKEN}/$SSLH_API_TOKEN/g" config/worker_production.json
        fi
    fi

    # Create required directories
    mkdir -p /tmp/sslh-worker-data
    mkdir -p /tmp/sslh-workspace
    mkdir -p logs

    print_success "Production configuration updated."
}

# =============================================================================
# 7. Database Setup
# =============================================================================
setup_database() {
    print_status "Setting up database..."

    # Ask user if they want to reset the database
    read -p "Do you want to reset the database? This will clear all existing data. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Resetting database..."
        rm -f db.sqlite3
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
}

# =============================================================================
# 8. Create Superuser
# =============================================================================
create_superuser() {
    print_status "Setting up Django superuser..."

    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>/dev/null; then
        print_success "Superuser already exists."
        return
    fi

    # Create superuser automatically
    print_status "Creating superuser (admin/admin)..."
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')" | python manage.py shell

    print_success "Superuser created: $DJANGO_SUPERUSER_USERNAME"
}

# =============================================================================
# 9. Create Authentication Token
# =============================================================================
create_auth_token() {
    print_status "Creating authentication token for API..."

    python manage.py shell << EOF
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Get or create admin user
user, created = User.objects.get_or_create(username='$DJANGO_SUPERUSER_USERNAME')

# Get or create token
token, created = Token.objects.get_or_create(user=user)

if created:
    print(f"Created new API token: {token.key}")
else:
    print(f"Using existing API token: {token.key}")

# Update the token in environment and config
import os
os.environ['SSLH_API_TOKEN'] = token.key

# Update production config with the actual Django token
import json
try:
    with open('config/worker_production.json', 'r') as f:
        config = json.load(f)
    
    config['API_TOKEN'] = token.key
    
    with open('config/worker_production.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Updated config/worker_production.json with Django API token")
except Exception as e:
    print(f"Warning: Could not update config file: {e}")
EOF

    print_success "API authentication token configured."
}

# =============================================================================
# 10. SSL Certificate Generation
# =============================================================================
setup_ssl_certificates() {
    print_status "Setting up SSL certificates..."

    if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
        print_status "Generating SSL certificates for HTTPS..."
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
            -subj "/C=US/ST=CA/L=San Francisco/O=SSLH-LabHub" --addext 'subjectAltName=IP:128.164.33.148' || {
            print_error "Failed to generate SSL certificates"
            exit 1
        }
        print_success "SSL certificates generated."
    else
        print_success "SSL certificates already exist."
    fi
}

# =============================================================================
# 11. Static Files Collection
# =============================================================================
collect_static_files() {
    print_status "Collecting static files..."
    python manage.py collectstatic --noinput || {
        print_warning "Static files collection failed or was skipped"
    }

    print_success "Static files collected."
}

# =============================================================================
# 12. Server Startup Functions
# =============================================================================
start_development_server() {
    print_status "Starting Django development server on port $DEFAULT_HTTP_PORT..."
    python manage.py runserver $DEFAULT_HTTP_PORT
}

start_gunicorn_http() {
    print_status "Starting Gunicorn HTTP server on port $DEFAULT_HTTP_PORT..."
    gunicorn --bind 0.0.0.0:$DEFAULT_HTTP_PORT \
             --workers $DEFAULT_WORKERS \
             --log-level info \
             --access-logfile logs/access.log \
             --error-logfile logs/error.log \
             labhub.wsgi:application
}

start_gunicorn_https() {
    local port=${1:-$DEFAULT_HTTPS_PORT}
    print_status "Starting Gunicorn HTTPS server on port $port..."
    gunicorn --bind 0.0.0.0:$port \
             --workers $DEFAULT_WORKERS \
             --certfile=cert.pem \
             --keyfile=key.pem \
             --log-level info \
             --access-logfile logs/access.log \
             --error-logfile logs/error.log \
             labhub.wsgi:application
}

start_worker() {
    print_status "Starting SSLH worker with production configuration..."
    if [ -f "sslh-dummy-worker.py" ]; then
        python3 sslh-dummy-worker.py -c config/worker_production.json
    else
        print_error "sslh-dummy-worker.py not found!"
        exit 1
    fi
}

start_detailed_worker() {
    print_status "Starting detailed worker..."
    if [ -f "sslh-detailed-worker.py" ]; then
        python3 sslh-detailed-worker.py -c config/worker_production.json
    else
        print_warning "sslh-detailed-worker.py not found, skipping detailed worker"
    fi
}

# =============================================================================
# 13. Main Deployment Function
# =============================================================================
main_deployment() {
    print_success "=== SSLH LabHub Production Deployment Starting ==="
    echo

    # Run all setup steps
    check_requirements
    setup_repository
    setup_virtual_environment
    install_dependencies
    setup_environment_variables
    update_production_config
    setup_database
    create_superuser
    create_auth_token
    setup_ssl_certificates
    collect_static_files

    print_success "=== Deployment Complete! ==="
    echo
    print_success "Configuration Summary:"
    echo "• Project: $PROJECT_DIR"
    echo "• Branch: $BRANCH_NAME"
    echo "• Virtual Environment: $VENV_NAME"
    echo "• Database: SQLite (db.sqlite3)"
    echo "• SSL Certificates: cert.pem, key.pem"
    echo "• API Token: $SSLH_API_TOKEN"
    echo "• Superuser: $DJANGO_SUPERUSER_USERNAME"
    echo
}

# =============================================================================
# 14. Server Startup Menu
# =============================================================================
show_startup_menu() {
    echo "Choose deployment option:"
    echo "1) Development server (HTTP on port $DEFAULT_HTTP_PORT)"
    echo "2) Gunicorn server (HTTP on port $DEFAULT_HTTP_PORT)"
    echo "3) Gunicorn server with HTTPS (port $DEFAULT_HTTPS_PORT) - PRODUCTION"
    echo "4) Worker only (connects to running server)"
    echo "5) Both server (HTTPS) and worker in background"
    echo "6) Setup complete - manual start"
    echo

    read -p "Enter your choice (1-6): " -n 1 -r
    echo

    case $REPLY in
        1)
            start_development_server
            ;;
        2)
            start_gunicorn_http
            ;;
        3)
            start_gunicorn_https
            ;;
        4)
            start_worker
            ;;
        5)
            print_status "Starting Gunicorn HTTPS server in background..."
            nohup gunicorn --bind 0.0.0.0:$DEFAULT_HTTPS_PORT \
                           --workers $DEFAULT_WORKERS \
                           --certfile=cert.pem \
                           --keyfile=key.pem \
                           --log-level info \
                           --access-logfile logs/access.log \
                           --error-logfile logs/error.log \
                           labhub.wsgi:application > logs/gunicorn.out 2>&1 &
            echo $! > gunicorn.pid
            
            sleep 3
            
            print_status "Starting worker..."
            start_worker
            ;;
        6)
            print_success "Setup complete. Manual startup commands:"
            echo
            echo "Development server:"
            echo "  python manage.py runserver $DEFAULT_HTTP_PORT"
            echo
            echo "Production HTTPS server:"
            echo "  gunicorn --bind 0.0.0.0:$DEFAULT_HTTPS_PORT --certfile=cert.pem --keyfile=key.pem --workers $DEFAULT_WORKERS labhub.wsgi:application"
            echo
            echo "Worker:"
            echo "  python3 sslh-dummy-worker.py -c config/worker_production.json"
            echo
            echo "Access URLs:"
            echo "  Admin: https://localhost:$DEFAULT_HTTPS_PORT/admin/"
            echo "  Job Submit: https://localhost:$DEFAULT_HTTPS_PORT/qmodel/submit/"
            echo "  API: https://localhost:$DEFAULT_HTTPS_PORT/qmodel/next-job/"
            ;;
        *)
            print_warning "Invalid choice. Setup complete but no server started."
            ;;
    esac
}

# =============================================================================
# 15. Final Instructions
# =============================================================================
show_final_instructions() {
    echo
    print_success "=== Production Deployment Summary ==="
    echo "• Server URL: https://localhost:$DEFAULT_HTTPS_PORT"
    echo "• Admin Panel: https://localhost:$DEFAULT_HTTPS_PORT/admin/"
    echo "• Job Submission: https://localhost:$DEFAULT_HTTPS_PORT/qmodel/submit/"
    echo "• API Endpoint: https://localhost:$DEFAULT_HTTPS_PORT/qmodel/next-job/"
    echo "• Worker Config: config/worker_production.json"
    echo
    echo "=== Credentials ==="
    echo "• Superuser: $DJANGO_SUPERUSER_USERNAME / $DJANGO_SUPERUSER_PASSWORD"
    echo "• API Token: $SSLH_API_TOKEN"
    echo
    echo "=== Multiple Terminal Setup ==="
    echo "Terminal 1 (Server): ./production-deploy.sh (choose option 3)"
    echo "Terminal 2 (Worker): source $VENV_NAME/bin/activate && python3 sslh-dummy-worker.py -c config/worker_production.json"
    echo
    echo "=== Log Files ==="
    echo "• Gunicorn Access: logs/access.log"
    echo "• Gunicorn Errors: logs/error.log"
    echo "• Background Output: logs/gunicorn.out"
    echo
    print_success "Production deployment ready! 🚀"
}

# =============================================================================
# 16. Script Entry Point
# =============================================================================

# Main execution
main_deployment

# Show startup menu
show_startup_menu

# Show final instructions
show_final_instructions
