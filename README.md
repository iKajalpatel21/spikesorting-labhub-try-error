# � QModel Spike Sorting Job Queue System

*Last updated: August 18, 2025*

---

## 📌 Overview

A production-ready, secure job queue system built with Django + Django REST Framework (DRF) for spike sorting job submissions and processing. This system includes:

* ✅ **Django REST API** with secure endpoints for job submission, fetching, and updating
* ✅ **Independent Python worker** that polls for jobs and processes them step-by-step
* ✅ **Production HTTPS** with Nginx reverse proxy and SSL/TLS termination
* ✅ **Gunicorn WSGI server** for high-performance Django deployment
* ✅ **Complete security stack** with HSTS, CSP, and modern TLS protocols

---

## 🗂️ Project Structure

```
spikesorting-labhub-try-error/
├── labhub/                     # Django project config
│   ├── settings_production.py  # Production settings with SSL security
│   ├── settings.py             # Development settings
│   └── urls.py                 # Routes requests to qmodel app
│
├── qmodel/                     # Core app for job processing
│   ├── models.py               # Job, JobStep, StepConfig models
│   ├── views.py                # API logic (submit, fetch, update jobs)
│   ├── serializers.py          # DRF serializers
│   └── urls.py                 # API routes
│
├── ssl/                        # SSL/TLS certificates
│   ├── certificate.crt         # SSL certificate
│   ├── private.key             # Private key
│   └── dhparam.pem             # Diffie-Hellman parameters
│
├── logs/                       # Application logs
├── staticfiles/                # Collected static files
├── qmodel_worker_production.py # Production worker with SSL support
├── nginx_qmodel.conf           # Nginx configuration
├── gunicorn.conf.py            # Gunicorn production configuration
├── .env                        # Environment configuration
└── requirements_production.txt
```

---

## ⚙️ Production Features

* ✅ **Token-authenticated API** using DRF TokenAuthentication
* ✅ **SSL/TLS encryption** with TLS 1.3 and HTTP/2 support
* ✅ **Security headers** (HSTS, CSP, XSS protection, etc.)
* ✅ **Job processing pipeline** with configurable steps
* ✅ **Production logging** and monitoring
* ✅ **Process management** with systemd services
* ✅ **Nginx reverse proxy** with SSL termination

---

## � Authentication & Security

* **HTTPS/TLS 1.3** with strong cipher suites
* **HTTP/2** for improved performance
* **HSTS** (HTTP Strict Transport Security) with 1-year max-age
* **Security headers** for XSS, clickjacking, and content type protection
* **Token-based API authentication**

---

## � Job Processing Pipeline

```
Job Submission → Status: pending
  ⇩
Worker fetches → Status: fetched  
  ⇩
Processing starts → Status: running
  ⇩
Step completion → Status: completed (per step)
  ⇩
All steps done → Status: finished
```

---

## � Production Deployment

### Prerequisites
- Python 3.8+
- Nginx (installed via Homebrew)
- SSL certificates (self-signed for development)

### Quick Start

```bash
# 1. Run the automated deployment script
./deploy_production.sh

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your settings

# 3. Install dependencies
pip install -r requirements_production.txt

# 4. Setup database
python manage.py migrate --settings=labhub.settings_production

# 5. Collect static files
python manage.py collectstatic --noinput --settings=labhub.settings_production
```

### Service Management

Use the provided service management script for easy control:

```bash
# Check service status
./qmodel_services.sh status

# Start all services
./qmodel_services.sh start

# Stop all services  
./qmodel_services.sh stop

# Restart services
./qmodel_services.sh restart

# Start worker
./qmodel_services.sh worker
```

### Manual Service Management

```bash
# Start services (production)
nginx
DJANGO_SETTINGS_MODULE=labhub.settings_production \
  .venv/bin/python -m gunicorn --bind 127.0.0.1:8000 labhub.wsgi:application --daemon

# Start worker
.venv/bin/python qmodel_worker_production.py

# Stop services
nginx -s quit
pkill -f gunicorn
pkill -f qmodel_worker_production
```

### Health Checks

```bash
# Test HTTPS stack
curl -k https://localhost/health/
# Returns: healthy

# Test API endpoint
curl -k https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token e1997396f5c992a1cc89ea5c8a518ab22bbab65f"

# Check SSL certificate
echo | openssl s_client -connect localhost:443 -servername localhost
```

---

## � API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/qmodel/getthenextjob/` | GET/POST | Fetch next job or update job status |
| `/health/` | GET | Health check endpoint |
| `/admin/` | GET | Django admin interface |

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API URLs, tokens, SSL settings) |
| `labhub/settings_production.py` | Production Django settings with security |
| `gunicorn.conf.py` | Gunicorn WSGI server configuration |
| `nginx_qmodel.conf` | Nginx reverse proxy with SSL/TLS |
| `qmodel-django.service` | Systemd service for Django app |
| `qmodel-worker.service` | Systemd service for background worker |

---

## � Environment Configuration

Example `.env` file:
```bash
# Django Configuration
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# API Configuration  
API_URL=https://localhost/qmodel/getthenextjob/
AUTH_TOKEN=e1997396f5c992a1cc89ea5c8a518ab22bbab65f

# SSL/TLS Configuration
SSL_VERIFY=false  # Set to true with real certificates

# Logging
LOG_LEVEL=INFO
LOG_FILE=qmodel_worker.log
```

---

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Stop existing nginx
nginx -s quit

# Check for processes using ports
lsof -i :80
lsof -i :443

# Kill specific processes if needed
pkill -f nginx
```

### SSL Certificate Issues
```bash
# Regenerate certificates
./generate_ssl_certs.sh

# Test certificate validity
openssl x509 -in ssl/certificate.crt -text -noout
```

### Worker Connection Issues
```bash
# Check worker logs
tail -f qmodel_worker.log

# Test API connectivity
curl -k https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token your-token"
```

---

## � Documentation

- **[Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)** - Complete setup instructions
- **[SSL/TLS Test Results](SSL_TEST_RESULTS.md)** - Security testing documentation  
- **[HTTPS Stack Test Results](HTTPS_STACK_TEST_RESULTS.md)** - Complete stack testing

---

## 📚 Acknowledgements

Built in the Laboratory of Systems Neural Development at George Washington University. This production-ready system demonstrates secure job queuing, API-driven worker orchestration, and spike sorting pipeline foundations with enterprise-grade security and deployment practices.