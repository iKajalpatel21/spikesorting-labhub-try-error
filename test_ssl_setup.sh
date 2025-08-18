#!/bin/bash

# SSL/TLS Testing Script for QModel Production Setup
# This script helps test the SSL/TLS configuration step by step

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo "=========================================="
echo "QModel SSL/TLS Testing Script"
echo "=========================================="

# Test 1: Check if SSL certificates exist
print_status "Checking SSL certificates..."
if [ -f "ssl/qmodel.crt" ] && [ -f "ssl/qmodel.key" ]; then
    print_success "SSL certificates found"
    
    # Check certificate details
    print_info "Certificate details:"
    openssl x509 -in ssl/qmodel.crt -text -noout | grep -E "(Subject:|Not Before:|Not After:|DNS:)"
    
    # Check if certificate is valid
    if openssl x509 -checkend 86400 -noout -in ssl/qmodel.crt; then
        print_success "Certificate is valid for at least 24 hours"
    else
        print_warning "Certificate expires within 24 hours"
    fi
else
    print_error "SSL certificates not found. Generating them now..."
    if [ -f "generate_ssl_certs.sh" ]; then
        chmod +x generate_ssl_certs.sh
        ./generate_ssl_certs.sh
        print_success "SSL certificates generated"
    else
        print_error "generate_ssl_certs.sh not found"
        exit 1
    fi
fi

# Test 2: Check if required directories exist
print_status "Checking required directories..."
for dir in "logs" "ssl"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_info "Created directory: $dir"
    else
        print_success "Directory exists: $dir"
    fi
done

# Test 3: Check if .env file exists
print_status "Checking environment configuration..."
if [ -f ".env" ]; then
    print_success ".env file exists"
    
    # Check for required SSL-related variables
    if grep -q "SSL_VERIFY" .env; then
        ssl_verify=$(grep "SSL_VERIFY" .env | cut -d'=' -f2)
        print_info "SSL_VERIFY is set to: $ssl_verify"
    else
        print_warning "SSL_VERIFY not found in .env"
    fi
    
    if grep -q "API_URL" .env; then
        api_url=$(grep "API_URL" .env | cut -d'=' -f2)
        print_info "API_URL is set to: $api_url"
        if [[ $api_url == https://* ]]; then
            print_success "API_URL uses HTTPS"
        else
            print_warning "API_URL does not use HTTPS"
        fi
    fi
else
    print_warning ".env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Created .env from template. Please edit it with your settings."
    fi
fi

# Test 4: Test Gunicorn configuration
print_status "Testing Gunicorn configuration..."
if command -v gunicorn &> /dev/null; then
    if gunicorn --check-config labhub.wsgi:application; then
        print_success "Gunicorn configuration is valid"
    else
        print_error "Gunicorn configuration has errors"
    fi
else
    print_error "Gunicorn not installed. Run: pip install gunicorn"
fi

# Test 5: Test Django production settings
print_status "Testing Django production settings..."
if python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'labhub.settings_production')
import django
django.setup()
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'SECURE_SSL_REDIRECT: {getattr(settings, \"SECURE_SSL_REDIRECT\", False)}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
"; then
    print_success "Django production settings loaded successfully"
else
    print_error "Error loading Django production settings"
fi

# Test 6: Check Nginx configuration syntax
print_status "Testing Nginx configuration..."
if [ -f "nginx_qmodel.conf" ]; then
    print_success "Nginx configuration file exists"
    
    # Test with nginx if available
    if command -v nginx &> /dev/null; then
        # Copy config to temporary location for testing
        temp_conf="/tmp/nginx_qmodel_test.conf"
        cp nginx_qmodel.conf "$temp_conf"
        
        if nginx -t -c "$temp_conf" 2>/dev/null; then
            print_success "Nginx configuration syntax is valid"
        else
            print_warning "Nginx configuration may have syntax issues"
        fi
        rm -f "$temp_conf"
    else
        print_info "Nginx not installed - skipping syntax check"
    fi
else
    print_error "nginx_qmodel.conf not found"
fi

echo ""
echo "=========================================="
echo "Manual Testing Steps"
echo "=========================================="

echo ""
print_info "1. Start Gunicorn with SSL-ready Django:"
echo "   gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application --settings=labhub.settings_production"

echo ""
print_info "2. Test Django SSL redirects (should redirect to HTTPS):"
echo "   curl -I http://localhost:8000/admin/ -H 'Host: yourdomain.com'"

echo ""
print_info "3. Test API endpoint directly (HTTP):"
echo "   curl -X GET http://localhost:8000/qmodel/getthenextjob/ \\"
echo "        -H 'Authorization: Token e1997396f5c992a1cc89ea5c8a518ab22bbab65f'"

echo ""
print_info "4. Start Nginx (after installing and configuring):"
echo "   sudo nginx -t  # Test configuration"
echo "   sudo systemctl start nginx"

echo ""
print_info "5. Test HTTPS through Nginx:"
echo "   curl -k https://localhost/qmodel/getthenextjob/ \\"
echo "        -H 'Authorization: Token e1997396f5c992a1cc89ea5c8a518ab22bbab65f'"

echo ""
print_info "6. Test SSL certificate details:"
echo "   openssl s_client -connect localhost:443 -servername localhost"

echo ""
print_info "7. Test worker with SSL API:"
echo "   python3 qmodel_worker_production.py"

echo ""
print_info "8. Check SSL security headers:"
echo "   curl -I -k https://localhost/"

echo ""
print_info "9. Test with SSL Labs (for real domains):"
echo "   https://www.ssllabs.com/ssltest/"

echo ""
echo "=========================================="
echo "SSL/TLS Testing Complete"
echo "=========================================="
