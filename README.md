# 🧪 hello-drf Branch – Django REST API with HTTPS

_Last updated: June 13, 2025_

---

## 📌 What This Branch Does

This branch includes a complete working setup for:

- ✅ A Django REST Framework API to submit and list "Experiment" jobs
- ✅ HTTPS using self-signed SSL/TLS certs (via Uvicorn)
- ✅ Static files support via `collectstatic`

---

## ⚙️ Key Features Implemented

- Django project and app structure: `labhub/`, `spikejobs/`
- `Experiment` model with fields `name` and `created_at`
- DRF ViewSet + Router to handle API routes
- API endpoint:  
  `https://127.0.0.1:8443/api/experiments/`
- Self-signed certs: `cert.pem`, `key.pem`
- Static files collected and served

---

## 🚀 Run the App with HTTPS Locally

Make sure your virtualenv is activated.

### 1. Generate a self-signed cert (for local HTTPS)

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
```

### 2. Install Uvicorn if needed
```bash
pip install uvicorn
```

### 3. Run the secure server
```bash
uvicorn labhub.asgi:application \
  --host 127.0.0.1 --port 8443 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```
Then open in browser: https://127.0.0.1:8443/api/experiments/

---

Directory Overview:
```
spikesorting-labhub-try-error/
│
├── labhub/               # Django project folder
│   ├── settings.py       # Includes STATIC_ROOT config
│   └── urls.py           # Includes route to `spikejobs`
│
├── spikejobs/            # Django app for experiment jobs
│   ├── models.py         # Experiment model
│   ├── views.py          # DRF ViewSet
│   ├── urls.py           # API route definitions
│   └── serializers.py    # DRF serializer
│
├── staticfiles/          # Static files collected with `collectstatic`
│
├── cert.pem              # Self-signed certificate
├── key.pem               # Private key
└── requirements.txt

🔖 Notes
Browser may show Not Secure because it's a self-signed cert

Static files required:

STATIC_ROOT = BASE_DIR / "staticfiles"


Then collect with: python manage.py collectstatic


# SpikeSorting LabHub

A Django-based backend for managing spike sorting job submissions and tracking. Built using Django + DRF.

## Features

- Admin panel to view and manage jobs
- SQLite database with `Experiment` model
- Custom admin display with sorting and filtering
- Django REST Framework installed for future API work

## Setup Instructions

```bash
# Create DB
python manage.py makemigrations spikejobs
python manage.py migrate

# Create superuser 
python manage.py createsuperuser
Kajal/User@123


# Run server
python manage.py runserver

Admin Login
Go to http://127.0.0.1:8000/admin

Login with your superuser credentials