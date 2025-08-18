#!/bin/bash

# QModel Production Deployment Script
# This script sets up the production environment for the QModel Django application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root (not recommended for development)
if [[ $EUID -eq 0 ]]; then
   print_warning "This script is running as root. Consider using a non-root user for development."
fi

print_status "Starting QModel Production Deployment..."

# Step 1: Create production environment file
print_status "Step 1: Creating production environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from template"
    print_warning "Please edit .env file with your production values before continuing"
    echo "Press Enter when ready to continue..."
    read
else
    print_success ".env file already exists"
fi

# Step 2: Install production dependencies
print_status "Step 2: Installing production dependencies..."
if command -v python3 &> /dev/null; then
    pip3 install -r requirements_production.txt
    print_success "Production dependencies installed"
else
    print_error "Python3 not found. Please install Python 3.8+ and try again."
    exit 1
fi

# Step 3: Run Django migrations
print_status "Step 3: Running Django database migrations..."
python3 manage.py migrate --settings=labhub.settings_production
print_success "Database migrations completed"

# Step 4: Collect static files
print_status "Step 4: Collecting static files..."
python3 manage.py collectstatic --noinput --settings=labhub.settings_production
print_success "Static files collected"

# Step 5: Generate SSL certificates (development only)
print_status "Step 5: Generating SSL certificates for development..."
if [ ! -f ssl/qmodel.crt ] || [ ! -f ssl/qmodel.key ]; then
    chmod +x generate_ssl_certs.sh
    ./generate_ssl_certs.sh
    print_success "SSL certificates generated"
else
    print_success "SSL certificates already exist"
fi

# Step 6: Test Gunicorn configuration
print_status "Step 6: Testing Gunicorn configuration..."
gunicorn --check-config labhub.wsgi:application
print_success "Gunicorn configuration is valid"

# Step 7: Setup systemd services (requires sudo)
print_status "Step 7: Setting up systemd services..."
if command -v systemctl &> /dev/null; then
    print_warning "The following commands require sudo privileges:"
    echo "sudo cp qmodel-django.service /etc/systemd/system/"
    echo "sudo cp qmodel-worker.service /etc/systemd/system/"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable qmodel-django"
    echo "sudo systemctl enable qmodel-worker"
    echo ""
    echo "Run these commands manually with sudo if you want to enable systemd services."
else
    print_warning "systemctl not available. Skipping systemd service setup."
fi

# Step 8: Setup Nginx (requires sudo)
print_status "Step 8: Nginx configuration..."
if command -v nginx &> /dev/null; then
    print_warning "To setup Nginx, run the following commands with sudo:"
    echo "sudo cp nginx_qmodel.conf /etc/nginx/sites-available/qmodel"
    echo "sudo ln -s /etc/nginx/sites-available/qmodel /etc/nginx/sites-enabled/"
    echo "sudo nginx -t  # Test configuration"
    echo "sudo systemctl reload nginx"
else
    print_warning "Nginx not installed. Please install nginx and configure manually."
fi

print_success "Production deployment setup completed!"

echo ""
print_status "Next steps:"
echo "1. Edit .env file with your production settings"
echo "2. Test the application with: gunicorn labhub.wsgi:application"
echo "3. Start the worker with: python3 qmodel_worker_production.py"
echo "4. Configure and start Nginx for SSL/TLS termination"
echo "5. Enable and start systemd services for production"

echo ""
print_status "Useful commands:"
echo "  Test Gunicorn: gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application"
echo "  Start worker: python3 qmodel_worker_production.py"
echo "  Check logs: tail -f qmodel_worker.log"
echo "  Test SSL: curl -k https://localhost/qmodel/getthenextjob/"

print_success "Deployment script completed successfully!"
