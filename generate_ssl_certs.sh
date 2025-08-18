#!/bin/bash

# SSL Certificate Generation Script for QModel
# For production, use certificates from a trusted CA like Let's Encrypt

echo "🔒 SSL Certificate Generation for QModel"
echo "========================================"

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate private key
echo "📝 Generating private key..."
openssl genrsa -out ssl/private.key 2048

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new -key ssl/private.key -out ssl/certificate.csr \
    -subj "/C=US/ST=State/L=City/O=QModel Lab/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
echo "📝 Generating self-signed certificate..."
openssl x509 -req -days 365 -in ssl/certificate.csr \
    -signkey ssl/private.key -out ssl/certificate.crt

# Create Diffie-Hellman parameters for extra security
echo "📝 Generating Diffie-Hellman parameters..."
openssl dhparam -out ssl/dhparam.pem 2048

# Set appropriate permissions
chmod 600 ssl/private.key
chmod 644 ssl/certificate.crt
chmod 644 ssl/dhparam.pem

echo "✅ SSL certificates generated successfully!"
echo ""
echo "📁 Generated files:"
echo "   ssl/private.key     - Private key"
echo "   ssl/certificate.crt - Certificate"
echo "   ssl/certificate.csr - Certificate signing request"
echo "   ssl/dhparam.pem     - Diffie-Hellman parameters"
echo ""
echo "⚠️  IMPORTANT: These are self-signed certificates for development only!"
echo "   For production, obtain certificates from a trusted CA like Let's Encrypt."
echo ""
echo "🚀 Next steps:"
echo "   1. Configure Nginx to use these certificates"
echo "   2. Start Gunicorn: gunicorn --config gunicorn.conf.py labhub.wsgi:application"
echo "   3. Configure and start Nginx"
