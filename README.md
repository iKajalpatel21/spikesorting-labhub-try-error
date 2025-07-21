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


# Spike Sorting LabHub – Toy Demo

This project is a toy example for managing and processing spike sorting jobs via a Django-based backend and an independent Python worker.

---

## 🚀 Project Structure

- **Frontend (HTML):** Submits a `.json` job file.
- **Backend (Django REST API):** Receives, stores, and updates job status.
- **Worker (`worker.py`):** Polls the API for pending jobs, processes them, and updates their result and log.

---

## 🧠 How It Works

1. Users submit JSON job files via the frontend form.
2. Jobs are stored with `"pending"` status in the Django backend (Experiment model).
3. The Python worker continuously polls the API:
   - Fetches a pending job.
   - Parses job parameters.
   - Simulates processing with `time.sleep(a)`.
   - Generates a result and a log file in the `/results/` directory.
   - Updates the job status to `"finished"` and attaches file paths.

---

## 📂 JSON Job Format

Example:
```json
{
  "parameters": {
    "a": 2,
    "b": 3
  }
}




## ✅ Features Implemented (Based on GitHub Setup Guide)

- [x] **Repo initialized** and structured with `backend/` and `worker.py`
- [x] **Django project setup** with REST API (DRF)
- [x] **Job model** with `status`, `result_path`, `log_path`, and submission timestamp
- [x] **Job submission endpoint** (`/api/experiment`) that accepts `.json` files
- [x] **Get-next-job endpoint** that returns the oldest `pending` job and marks it as `fetched`
- [x] **Job update endpoint** (`/api/experiment/<id>/`) to mark job as `running`, `finished`, or `failed`
- [x] **Frontend** with a form to upload `.json` jobs and see job list/status
- [x] **Worker script**:
  - Polls `/get-next`
  - Marks job as `running`
  - Sleeps for `a` seconds (from job JSON)
  - Saves dummy result/log paths
  - Marks job as `finished`
- [x] **Security**: API only accepts `.json`; jobs are processed sequentially

---

## 🔧 How to Run the Backend

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

## 🛠️ How to Run the Worker

```bash
python worker.py
```

---

## 📤 Sample Job JSON

```json
{
  "job_id": "test_001",
  "a": 5,
  "description": "Test spike sorting job"
}
```

---

## 🧪 Next Steps

- Add authentication (tokens) between backend and worker
- Save uploaded `.json` files on NAS (Truenas Scale integration)
- Run job using SpikeInterface instead of dummy sleep
- Add job retry or error handling with retry counters

---

## 📚 Acknowledgements

This project is developed in the Laboratory of Systems Neural Development at George Washington University. Inspired by the need for scalable, modular spike sorting infrastructure.
