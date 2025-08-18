#!/bin/bash

# QModel Service Management Script
# Easy control of production services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

PROJECT_DIR="/Users/kajalpatel/spikesorting-labhub-try-error"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
GUNICORN_PID="$PROJECT_DIR/gunicorn.pid"

start_services() {
    print_status "Starting QModel production services..."
    
    # Check if nginx is already running
    if pgrep nginx > /dev/null; then
        print_warning "Nginx is already running"
    else
        print_status "Starting Nginx..."
        nginx
        print_success "Nginx started"
    fi
    
    # Check if gunicorn is already running
    if [ -f "$GUNICORN_PID" ] && pgrep -F "$GUNICORN_PID" > /dev/null; then
        print_warning "Gunicorn is already running"
    else
        print_status "Starting Gunicorn..."
        cd "$PROJECT_DIR"
        DJANGO_SETTINGS_MODULE=labhub.settings_production \
            "$VENV_PYTHON" -m gunicorn \
            --bind 127.0.0.1:8000 \
            --daemon \
            --pid "$GUNICORN_PID" \
            labhub.wsgi:application
        print_success "Gunicorn started"
    fi
    
    print_success "All services started successfully!"
}

stop_services() {
    print_status "Stopping QModel production services..."
    
    # Stop nginx
    if pgrep nginx > /dev/null; then
        print_status "Stopping Nginx..."
        nginx -s quit
        print_success "Nginx stopped"
    else
        print_warning "Nginx is not running"
    fi
    
    # Stop gunicorn
    if [ -f "$GUNICORN_PID" ] && pgrep -F "$GUNICORN_PID" > /dev/null; then
        print_status "Stopping Gunicorn..."
        pkill -F "$GUNICORN_PID"
        rm -f "$GUNICORN_PID"
        print_success "Gunicorn stopped"
    else
        print_warning "Gunicorn is not running"
    fi
    
    # Stop worker if running
    if pgrep -f qmodel_worker_production > /dev/null; then
        print_status "Stopping QModel worker..."
        pkill -f qmodel_worker_production
        print_success "Worker stopped"
    fi
    
    print_success "All services stopped"
}

restart_services() {
    print_status "Restarting QModel production services..."
    stop_services
    sleep 2
    start_services
}

status_services() {
    print_status "Checking QModel service status..."
    
    # Check nginx
    if pgrep nginx > /dev/null; then
        print_success "Nginx: Running"
    else
        print_error "Nginx: Not running"
    fi
    
    # Check gunicorn
    if [ -f "$GUNICORN_PID" ] && pgrep -F "$GUNICORN_PID" > /dev/null; then
        print_success "Gunicorn: Running (PID: $(cat $GUNICORN_PID))"
    else
        print_error "Gunicorn: Not running"
    fi
    
    # Check worker
    if pgrep -f qmodel_worker_production > /dev/null; then
        print_success "Worker: Running"
    else
        print_warning "Worker: Not running"
    fi
    
    echo ""
    print_status "Testing HTTPS stack..."
    if curl -s -k https://localhost/health/ | grep -q "healthy"; then
        print_success "HTTPS stack: Working"
    else
        print_error "HTTPS stack: Not responding"
    fi
}

start_worker() {
    print_status "Starting QModel worker..."
    cd "$PROJECT_DIR"
    if pgrep -f qmodel_worker_production > /dev/null; then
        print_warning "Worker is already running"
    else
        nohup "$VENV_PYTHON" qmodel_worker_production.py > worker.log 2>&1 &
        print_success "Worker started in background"
    fi
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    worker)
        start_worker
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|worker}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Nginx and Gunicorn"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Check service status"
        echo "  worker  - Start background worker"
        exit 1
        ;;
esac
