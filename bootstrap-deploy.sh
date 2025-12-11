#!/bin/bash

# =============================================================================
# SSLH LabHub Bootstrap Deployment Script
# =============================================================================
# 
# This script provides a complete deployment solution for the SSLH LabHub
# spikesorting system with configuration-driven deployment capabilities.
#
# Usage:
#   ./bootstrap-deploy.sh [ENVIRONMENT] [OPTIONS]
#
# Environments:
#   local       - Local development setup (default)
#   production  - Production deployment
#   worker-only - Worker-only deployment
#
# Options:
#   --port PORT         - Server port (default: 8000 for local, 8443 for prod)
#   --ssl               - Enable SSL/HTTPS
#   --no-migrate        - Skip database migrations
#   --no-collectstatic  - Skip static file collection
#   --workers N         - Number of worker processes (default: 2)
#   --help              - Show this help message
#
# Example:
#   ./bootstrap-deploy.sh local --port 8000
#   ./bootstrap-deploy.sh production --ssl --workers 4
#   ./bootstrap-deploy.sh worker-only
#
# =============================================================================

set -e  # Exit on any error

# =============================================================================
# Configuration Variables
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="spikesorting-labhub"
ENVIRONMENT="${1:-local}"
DEFAULT_PORT_LOCAL=8000
DEFAULT_PORT_PROD=8443
PYTHON_VERSION="3.11"
VENV_DIR=".venv"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
PORT=""
USE_SSL=false
SKIP_MIGRATE=false
SKIP_COLLECTSTATIC=false
WORKER_PROCESSES=2
SHOW_HELP=false

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << 'EOF'
SSLH LabHub Bootstrap Deployment Script

Usage: ./bootstrap-deploy.sh [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
  local       Local development setup (default)
  production  Production deployment with Gunicorn
  worker-only Worker-only deployment (no Django server)

OPTIONS:
  --port PORT         Server port (default: 8000 for local, 8443 for prod)
  --ssl               Enable SSL/HTTPS
  --no-migrate        Skip database migrations
  --no-collectstatic  Skip static file collection
  --workers N         Number of Gunicorn worker processes (default: 2)
  --help              Show this help message

EXAMPLES:
  ./bootstrap-deploy.sh local
  ./bootstrap-deploy.sh local --port 9000
  ./bootstrap-deploy.sh production --ssl --workers 4
  ./bootstrap-deploy.sh worker-only

CONFIGURATION FILES:
  config/worker_local.json      - Local worker configuration
  config/worker_production.json - Production worker configuration
  config/detailed_worker_local.json - Detailed local worker config

REQUIREMENTS:
  - Python 3.11+
  - pip
  - Virtual environment support
  - Git (for deployment)

EOF
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python version: $PYTHON_VER"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_warning "Git is not installed (optional for deployment)"
    fi
    
    log_success "System requirements check passed"
}

create_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        log_info "Virtual environment already exists"
    else
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    log_success "pip upgraded"
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Dependencies installed from requirements.txt"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

setup_database() {
    if [ "$SKIP_MIGRATE" = true ]; then
        log_info "Skipping database migrations"
        return
    fi
    
    log_info "Setting up database..."
    
    # Make migrations
    python manage.py makemigrations
    log_info "Migrations created"
    
    # Apply migrations
    python manage.py migrate
    log_success "Database migrations applied"
    
    # Create superuser for production
    if [ "$ENVIRONMENT" = "production" ]; then
        create_superuser
    fi
}

create_superuser() {
    log_info "Setting up Django superuser..."
    
    # Check if superuser already exists
    if python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>/dev/null; then
        log_info "Superuser already exists"
        return
    fi
    
    # Get superuser credentials from environment or prompt
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
        log_info "Creating superuser from environment variables..."
        python manage.py createsuperuser --noinput \
            --username "$DJANGO_SUPERUSER_USERNAME" \
            --email "$DJANGO_SUPERUSER_EMAIL" 2>/dev/null || true
    else
        log_info "Creating default superuser (admin/admin)..."
        echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@localhost', 'admin') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell
    fi
    
    log_success "Superuser created successfully"
}

collect_static_files() {
    if [ "$SKIP_COLLECTSTATIC" = true ]; then
        log_info "Skipping static file collection"
        return
    fi
    
    log_info "Collecting static files..."
    python manage.py collectstatic --noinput
    log_success "Static files collected"
}

setup_ssl_certificates() {
    log_info "Setting up SSL certificates..."
    
    if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
        log_info "Generating self-signed SSL certificates..."
        openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

create_directories() {
    log_info "Creating required directories..."
    
    # Worker directories from config
    mkdir -p /tmp/sslh-worker/data
    mkdir -p /tmp/local-workspace
    mkdir -p /tmp/sslh-workspace
    mkdir -p logs
    mkdir -p spikejobs
    
    log_success "Required directories created"
}

setup_production_environment() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return
    fi
    
    log_info "Setting up production environment..."
    
    # Set default environment variables if not provided
    export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-labhub.settings}"
    export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')}"
    
    # Set superuser defaults if not provided
    export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
    export DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-admin@localhost}"
    export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin}"
    
    # Set API token if not provided
    if [ -z "$SSLH_API_TOKEN" ]; then
        export SSLH_API_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(20))')"
        log_info "Generated API token: $SSLH_API_TOKEN"
        log_warning "Save this token for worker configuration!"
    fi
    
    # Update production config with actual token
    if [ -f "config/worker_production.json" ]; then
        sed -i.backup "s/\${SSLH_API_TOKEN}/$SSLH_API_TOKEN/g" config/worker_production.json
        log_success "Updated production configuration with API token"
    fi
    
    log_success "Production environment configured"
}

validate_configuration() {
    log_info "Validating configuration files..."
    
    local config_files=()
    
    case $ENVIRONMENT in
        "local")
            config_files=("config/worker_local.json" "config/detailed_worker_local.json")
            ;;
        "production")
            config_files=("config/worker_production.json")
            ;;
        "worker-only")
            config_files=("config/worker_local.json" "config/detailed_worker_local.json")
            ;;
    esac
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            # For production, substitute environment variables first
            if [ "$ENVIRONMENT" = "production" ] && [ "$config_file" = "config/worker_production.json" ]; then
                # Validate after environment variable substitution
                if envsubst < "$config_file" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
                    log_success "Configuration valid: $config_file"
                else
                    log_error "Invalid JSON in: $config_file (after environment substitution)"
                    exit 1
                fi
            else
                if python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
                    log_success "Configuration valid: $config_file"
                else
                    log_error "Invalid JSON in: $config_file"
                    exit 1
                fi
            fi
        else
            log_error "Configuration file missing: $config_file"
            exit 1
        fi
    done
}

start_django_server() {
    local port=$1
    
    log_info "Starting Django server on port $port..."
    
    case $ENVIRONMENT in
        "local")
            log_info "Starting development server..."
            python manage.py runserver "$port" &
            echo $! > django.pid
            ;;
        "production")
            log_info "Starting Gunicorn server with $WORKER_PROCESSES workers..."
            if [ "$USE_SSL" = true ]; then
                gunicorn --bind "0.0.0.0:$port" \
                         --workers "$WORKER_PROCESSES" \
                         --keyfile key.pem \
                         --certfile cert.pem \
                         --daemon \
                         --pid-file django.pid \
                         --log-file logs/gunicorn.log \
                         labhub.wsgi:application
            else
                gunicorn --bind "0.0.0.0:$port" \
                         --workers "$WORKER_PROCESSES" \
                         --daemon \
                         --pid-file django.pid \
                         --log-file logs/gunicorn.log \
                         labhub.wsgi:application
            fi
            ;;
    esac
    
    sleep 3
    
    # Check if server is running
    if [ "$USE_SSL" = true ]; then
        local protocol="https"
    else
        local protocol="http"
    fi
    
    local url="$protocol://127.0.0.1:$port/qmodel/jobs/"
    if curl -s -k --connect-timeout 5 "$url" > /dev/null; then
        log_success "Django server started successfully on $protocol://127.0.0.1:$port"
    else
        log_error "Failed to start Django server"
        exit 1
    fi
}

start_worker() {
    log_info "Starting SSLH worker..."
    
    local config_file=""
    case $ENVIRONMENT in
        "local")
            config_file="config/worker_local.json"
            ;;
        "production")
            config_file="config/worker_production.json"
            ;;
        "worker-only")
            config_file="config/worker_local.json"
            ;;
    esac
    
    if [ -f "sslh-dummy-worker.py" ]; then
        python3 sslh-dummy-worker.py -c "$config_file" &
        echo $! > worker.pid
        log_success "SSLH worker started with config: $config_file"
    else
        log_error "sslh-dummy-worker.py not found"
        exit 1
    fi
}

start_detailed_worker() {
    log_info "Starting detailed worker..."
    
    local config_file="config/detailed_worker_local.json"
    
    if [ -f "sslh-detailed-worker.py" ]; then
        python3 sslh-detailed-worker.py -c "$config_file" &
        echo $! > detailed-worker.pid
        log_success "Detailed worker started with config: $config_file"
    else
        log_warning "sslh-detailed-worker.py not found, skipping detailed worker"
    fi
}

stop_services() {
    log_info "Stopping services..."
    
    # Stop Django server
    if [ -f "django.pid" ]; then
        if kill -0 "$(cat django.pid)" 2>/dev/null; then
            kill "$(cat django.pid)"
            rm -f django.pid
            log_success "Django server stopped"
        fi
    fi
    
    # Stop workers
    if [ -f "worker.pid" ]; then
        if kill -0 "$(cat worker.pid)" 2>/dev/null; then
            kill "$(cat worker.pid)"
            rm -f worker.pid
            log_success "SSLH worker stopped"
        fi
    fi
    
    if [ -f "detailed-worker.pid" ]; then
        if kill -0 "$(cat detailed-worker.pid)" 2>/dev/null; then
            kill "$(cat detailed-worker.pid)"
            rm -f detailed-worker.pid
            log_success "Detailed worker stopped"
        fi
    fi
}

show_status() {
    log_info "Service Status:"
    echo "==================="
    
    # Django server status
    if [ -f "django.pid" ] && kill -0 "$(cat django.pid)" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Django Server: Running (PID: $(cat django.pid))"
    else
        echo -e "${RED}✗${NC} Django Server: Stopped"
    fi
    
    # Worker status
    if [ -f "worker.pid" ] && kill -0 "$(cat worker.pid)" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} SSLH Worker: Running (PID: $(cat worker.pid))"
    else
        echo -e "${RED}✗${NC} SSLH Worker: Stopped"
    fi
    
    # Detailed worker status
    if [ -f "detailed-worker.pid" ] && kill -0 "$(cat detailed-worker.pid)" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Detailed Worker: Running (PID: $(cat detailed-worker.pid))"
    else
        echo -e "${RED}✗${NC} Detailed Worker: Stopped"
    fi
    
    echo "==================="
}

show_deployment_info() {
    local port=$1
    local protocol="http"
    
    if [ "$USE_SSL" = true ]; then
        protocol="https"
    fi
    
    log_success "Deployment completed successfully!"
    echo ""
    echo "=============================================================================  "
    echo -e "${BLUE}SSLH LabHub Deployment Information${NC}"
    echo "============================================================================="
    echo ""
    echo "Environment: $ENVIRONMENT"
    echo "Server URL: $protocol://127.0.0.1:$port"
    echo ""
    echo "Available Endpoints:"
    echo "  Job Submission:  $protocol://127.0.0.1:$port/qmodel/submit/"
    echo "  Job List:        $protocol://127.0.0.1:$port/qmodel/jobs/"
    echo "  Next Job API:    $protocol://127.0.0.1:$port/qmodel/next-job/"
    echo "  Status API:      $protocol://127.0.0.1:$port/qmodel/status/{job_id}/"
    echo ""
    echo "Configuration Files:"
    echo "  Worker Config:   config/worker_${ENVIRONMENT}.json"
    if [ "$ENVIRONMENT" = "local" ]; then
        echo "  Detailed Worker: config/detailed_worker_local.json"
    fi
    echo ""
    echo "Log Files:"
    echo "  Django Logs:     logs/gunicorn.log (production mode)"
    echo "  Worker Logs:     Terminal output or configure logging"
    echo ""
    echo "Management Commands:"
    echo "  Check Status:    ./bootstrap-deploy.sh status"
    echo "  Stop Services:   ./bootstrap-deploy.sh stop"
    echo "  Restart:         ./bootstrap-deploy.sh restart"
    echo ""
    echo "============================================================================="
}

# =============================================================================
# Command Line Argument Parsing
# =============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                PORT="$2"
                shift 2
                ;;
            --ssl)
                USE_SSL=true
                shift
                ;;
            --no-migrate)
                SKIP_MIGRATE=true
                shift
                ;;
            --no-collectstatic)
                SKIP_COLLECTSTATIC=true
                shift
                ;;
            --workers)
                WORKER_PROCESSES="$2"
                shift 2
                ;;
            --help)
                SHOW_HELP=true
                shift
                ;;
            status)
                show_status
                exit 0
                ;;
            stop)
                stop_services
                exit 0
                ;;
            restart)
                stop_services
                sleep 2
                # Re-run the script without special commands
                exec "$0" "$ENVIRONMENT"
                ;;
            *)
                if [[ "$1" =~ ^(local|production|worker-only)$ ]]; then
                    ENVIRONMENT="$1"
                else
                    log_error "Unknown argument: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# =============================================================================
# Main Deployment Logic
# =============================================================================

main() {
    # Parse command line arguments (skip first argument which is environment)
    if [ $# -gt 0 ]; then
        parse_arguments "$@"
    fi
    
    if [ "$SHOW_HELP" = true ]; then
        show_help
        exit 0
    fi
    
    # Set default port based on environment
    if [ -z "$PORT" ]; then
        case $ENVIRONMENT in
            "local")
                PORT=$DEFAULT_PORT_LOCAL
                ;;
            "production")
                PORT=$DEFAULT_PORT_PROD
                ;;
            "worker-only")
                PORT=$DEFAULT_PORT_LOCAL  # Not used but set for consistency
                ;;
        esac
    fi
    
    log_info "Starting SSLH LabHub deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Port: $PORT"
    log_info "SSL: $USE_SSL"
    echo ""
    
    # Setup trap to cleanup on exit
    trap stop_services EXIT
    
    # Run deployment steps
    check_requirements
    create_virtual_environment
    install_dependencies
    create_directories
    validate_configuration
    
    if [ "$ENVIRONMENT" != "worker-only" ]; then
        setup_database
        collect_static_files
        
        if [ "$USE_SSL" = true ]; then
            setup_ssl_certificates
        fi
        
        start_django_server "$PORT"
    fi
    
    # Start workers
    start_worker
    
    if [ "$ENVIRONMENT" = "local" ]; then
        start_detailed_worker
    fi
    
    # Show deployment information
    show_deployment_info "$PORT"
    
    # Keep the script running
    log_info "Services are running. Press Ctrl+C to stop all services."
    
    # Wait for user interrupt
    while true; do
        sleep 10
        # Optional: Add health checks here
    done
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Change to script directory
cd "$SCRIPT_DIR"

# Run main function with all arguments
main "$@"
