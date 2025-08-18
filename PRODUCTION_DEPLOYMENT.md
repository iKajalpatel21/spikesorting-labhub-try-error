# QModel Production Deployment Guide

This guide provides step-by-step instructions for deploying the QModel Django application in a production environment with Gunicorn and Nginx with SSL/TLS support.

## Overview

The production deployment includes:
- Django application served by Gunicorn WSGI server
- Nginx reverse proxy with SSL/TLS termination
- Background worker for job processing
- Systemd services for process management
- SSL/TLS encryption for secure communication
- Environment-based configuration management

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Nginx web server
- systemd (for Linux systems)
- SSL certificates (self-signed for development, CA-signed for production)

## Quick Start

1. **Run the deployment script:**
   ```bash
   chmod +x deploy_production.sh
   ./deploy_production.sh
   ```

2. **Configure environment variables in `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env with your production settings
   ```

3. **Start the services:**
   ```bash
   # Manual start for testing
   gunicorn labhub.wsgi:application
   python3 qmodel_worker_production.py
   ```

## Detailed Configuration

### 1. Environment Configuration

Create and configure your `.env` file:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost

# Database
DATABASE_URL=postgres://user:password@localhost:5432/qmodel_db

# API Configuration
API_URL=https://yourdomain.com/qmodel/getthenextjob/
AUTH_TOKEN=e1997396f5c992a1cc89ea5c8a518ab22bbab65f

# Worker Configuration
POLLING_INTERVAL_SECONDS=5
SSL_VERIFY=True
LOG_LEVEL=INFO
LOG_FILE=qmodel_worker.log

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### 2. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb qmodel_db
sudo -u postgres createuser qmodel_user --pwprompt

# Run migrations
python3 manage.py migrate --settings=labhub.settings_production
```

### 3. Static Files

```bash
# Collect static files for production
python3 manage.py collectstatic --noinput --settings=labhub.settings_production
```

### 4. SSL Certificate Generation

For development/testing (self-signed):
```bash
chmod +x generate_ssl_certs.sh
./generate_ssl_certs.sh
```

For production, obtain certificates from a Certificate Authority (Let's Encrypt, etc.).

### 5. Gunicorn Configuration

The `gunicorn.conf.py` file provides production-ready settings:
- Multiple worker processes
- Proper logging
- Security settings
- Performance optimizations

Test Gunicorn:
```bash
gunicorn --check-config labhub.wsgi:application
gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application
```

### 6. Nginx Configuration

Install and configure Nginx:

```bash
# Install Nginx (Ubuntu/Debian)
sudo apt update
sudo apt install nginx

# Copy configuration
sudo cp nginx_qmodel.conf /etc/nginx/sites-available/qmodel
sudo ln -s /etc/nginx/sites-available/qmodel /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Complete End-to-End Workflow Testing

### Full Pipeline with HTTPS

This section demonstrates the complete workflow from JSON job submission to worker processing with HTTPS.

#### 1. Setup Database and Services

```bash
# Setup database
python3 manage.py migrate --settings=labhub.settings_production
python3 manage.py collectstatic --noinput --settings=labhub.settings_production

# Start services using the management script
./qmodel_services.sh start

# Verify services are running
./qmodel_services.sh status
```

#### 2. Create Authentication Token

```bash
# Create superuser if not exists
python3 manage.py createsuperuser --settings=labhub.settings_production

# Create API token for worker authentication
python3 manage.py shell --settings=labhub.settings_production
```

In the Django shell:
```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Get or create user
user = User.objects.get(username='your_username')  # Replace with your username
token, created = Token.objects.get_or_create(user=user)
print(f"API Token: {token.key}")
```

#### 3. Submit Job via HTTPS API

```bash
# Submit a job via HTTPS API
curl -k -X POST https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_001",
    "steps": [
      {"identifier": "preprocess", "function": "preprocess_data"},
      {"identifier": "spike_detect", "function": "detect_spikes"},
      {"identifier": "cluster", "function": "cluster_spikes"}
    ]
  }'
```

#### 4. Start Worker and Monitor Processing

```bash
# Start worker in background
./qmodel_services.sh worker

# Monitor worker logs
tail -f qmodel_worker.log

# Check job status in database
python3 manage.py shell --settings=labhub.settings_production
```

#### 5. Verify in Database

In Django shell:
```python
from qmodel.models import Job, JobStep
from django.utils import timezone

# Check all jobs
jobs = Job.objects.all()
for job in jobs:
    print(f"Job {job.id}: {job.status} - {job.created_at}")
    
# Check job steps
for job in jobs:
    steps = JobStep.objects.filter(job=job)
    for step in steps:
        print(f"  Step {step.identifier}: {step.status}")
```

#### 6. Complete Workflow Test

```bash
# Test complete workflow with script
./test_complete_workflow.sh
```

### 7. Systemd Services

Set up systemd services for automatic startup and monitoring:

```bash
# Copy service files
sudo cp qmodel-django.service /etc/systemd/system/
sudo cp qmodel-worker.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable qmodel-django
sudo systemctl enable qmodel-worker
sudo systemctl start qmodel-django
sudo systemctl start qmodel-worker

# Check status
sudo systemctl status qmodel-django
sudo systemctl status qmodel-worker
```

## Production Worker

The production worker (`qmodel_worker_production.py`) includes:
- SSL/TLS support with certificate verification
- Environment-based configuration
- Comprehensive logging
- Connection retry strategies
- Error handling and recovery

Start the worker:
```bash
python3 qmodel_worker_production.py
```

## Monitoring and Logging

### Check Application Logs

```bash
# Django application logs
sudo journalctl -u qmodel-django -f

# Worker logs
sudo journalctl -u qmodel-worker -f
tail -f qmodel_worker.log

# Nginx logs
sudo tail -f /var/log/nginx/qmodel_access.log
sudo tail -f /var/log/nginx/qmodel_error.log
```

### Health Checks

```bash
# Test API endpoint
curl -k https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token e1997396f5c992a1cc89ea5c8a518ab22bbab65f"

# Check process status
sudo systemctl status qmodel-django qmodel-worker nginx
```

## Security Considerations

### SSL/TLS Configuration
- Uses TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS (HTTP Strict Transport Security)
- Secure headers (X-Frame-Options, X-Content-Type-Options, etc.)

### Django Security Settings
- `SECURE_SSL_REDIRECT=True`
- `SECURE_PROXY_SSL_HEADER` for reverse proxy
- `CSRF_COOKIE_SECURE=True`
- `SESSION_COOKIE_SECURE=True`

### Firewall Configuration
```bash
# Allow HTTP and HTTPS traffic
sudo ufw allow 80
sudo ufw allow 443

# Block direct access to Django port
sudo ufw deny 8000
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors:**
   ```bash
   # Check certificate validity
   openssl x509 -in ssl/qmodel.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect localhost:443
   ```

2. **Permission Errors:**
   ```bash
   # Fix static file permissions
   sudo chown -R www-data:www-data /path/to/staticfiles/
   sudo chmod -R 755 /path/to/staticfiles/
   ```

3. **Database Connection Issues:**
   ```bash
   # Test database connection
   python3 manage.py dbshell --settings=labhub.settings_production
   ```

4. **Worker Not Processing Jobs:**
   ```bash
   # Check worker logs
   tail -f qmodel_worker.log
   
   # Test API directly
   curl -X GET https://localhost/qmodel/getthenextjob/ \
     -H "Authorization: Token your-token-here"
   ```

### Performance Tuning

1. **Gunicorn Workers:**
   - Adjust `workers` in `gunicorn.conf.py` based on CPU cores
   - Monitor memory usage and adjust `max_requests`

2. **Database Optimization:**
   - Configure PostgreSQL connection pooling
   - Optimize database queries
   - Set up database indexing

3. **Nginx Optimization:**
   - Enable gzip compression
   - Set appropriate cache headers
   - Configure rate limiting

## Backup and Maintenance

### Database Backup
```bash
# Create backup
pg_dump qmodel_db > qmodel_backup_$(date +%Y%m%d).sql

# Restore backup
psql qmodel_db < qmodel_backup_20231201.sql
```

### Log Rotation
```bash
# Configure logrotate for worker logs
sudo nano /etc/logrotate.d/qmodel-worker
```

### Updates and Maintenance
```bash
# Update dependencies
pip3 install -r requirements_production.txt --upgrade

# Run migrations
python3 manage.py migrate --settings=labhub.settings_production

# Restart services
sudo systemctl restart qmodel-django qmodel-worker
```

## Files Overview

| File | Purpose |
|------|---------|
| `labhub/settings_production.py` | Production Django settings |
| `gunicorn.conf.py` | Gunicorn WSGI server configuration |
| `nginx_qmodel.conf` | Nginx reverse proxy configuration |
| `qmodel-django.service` | Systemd service for Django app |
| `qmodel-worker.service` | Systemd service for background worker |
| `qmodel_worker_production.py` | Production worker with SSL support |
| `generate_ssl_certs.sh` | SSL certificate generation script |
| `.env.example` | Environment configuration template |
| `requirements_production.txt` | Production Python dependencies |
| `deploy_production.sh` | Automated deployment script |

This setup provides a robust, secure, and scalable production environment for the QModel application.
