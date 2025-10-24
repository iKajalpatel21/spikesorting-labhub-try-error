<!-- # 🧪 hello-drf Branch – Django REST API with HTTPS

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
  --host 127.0.0.1 --port 8000 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```
Then open in browser: https://127.0.0.1:8000/api/experiments/

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

This project is developed in the Laboratory of Systems Neural Development at George Washington University. Inspired by the need for scalable, modular spike sorting infrastructure. -->


# 🧠 Spike Sorting LabHub – Toy Job Queue System (hello-drf Branch)

*Last updated: July 21, 2025*

---

## 📌 Overview

A secure, minimal job queue demo system built with Django + Django REST Framework (DRF) to simulate spike sorting submissions and processing. This toy system includes:

* ✅ Django REST API with secure endpoints for job submission, fetching, and updating.
* ✅ Independent Python `worker.py` that polls for jobs and simulates processing.
* ✅ HTTPS support using self-signed certificates via Uvicorn.
* ✅ Static file handling and basic frontend for `.json` upload.

---

## 🗂️ Project Structure

```
spikesorting-labhub-try-error/
├── labhub/                 # Django project config
│   ├── settings.py         # Includes STATIC_ROOT
│   └── urls.py             # Routes requests to app
│
├── spikejobs/              # Core app for experiments
│   ├── models.py           # Experiment model (status, params, result_path)
│   ├── views.py            # API logic (submit, fetch, update)
│   ├── serializers.py      # DRF serializers
│   └── urls.py             # API routes
│
├── templates/              # HTML form for .json submission
│   └── submit_json.html
│
├── static/                 # Background image & assets
├── staticfiles/            # Collected static files
├── results/                # Output results & logs from worker
├── cert.pem / key.pem      # Self-signed HTTPS certificate + key
├── db.sqlite3              # SQLite database
├── worker.py               # Polling and job processing logic
├── README.md               # This file
└── requirements.txt
```

---

## ⚙️ Features Implemented

* ✅ Token-authenticated endpoints using DRF TokenAuthentication
* ✅ `Experiment` model with:

  * `status`: pending / fetched / running / finished / failed
  * `a`, `b`: optional job params
  * `result_path`, `logs`
* ✅ Secure GET `/api/experiments/get-next/` – returns the next pending job
* ✅ Secure POST `/api/experiments/<id>/` – updates job status and results
* ✅ HTML form at `/submit/` to upload `.json` job files
* ✅ Static background image served using `{% static %}`
* ✅ Worker polls API, updates job status, saves result/logs

---

## 🔐 Authentication & HTTPS

* HTTPS enabled using:

```bash
uvicorn labhub.asgi:application --host 127.0.0.1 --port 8000 \
    --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

* Worker uses:

```python
TOKEN = "<your-token>"
HEADERS = {"Authorization": f"Token {TOKEN}"}
requests.get(..., headers=HEADERS, verify="cert.pem")
```

---

## 🧪 Job Lifecycle

```
Frontend uploads job.json --> status: pending
  ⇩
Worker polls /get-next   --> status: fetched
  ⇩
Worker starts job        --> status: running
  ⇩
Worker saves result/log  --> status: finished
```

---

## 🚀 Quickstart Guide

### Setup and Run Backend (HTTPS)

```bash
# 1. Create DB
python manage.py makemigrations
python manage.py migrate

# 2. Create superuser (for admin)
python manage.py createsuperuser

# 3. Collect static files
python manage.py collectstatic

# 4. Run secure backend
uvicorn labhub.asgi:application --host 127.0.0.1 --port 8000 \
    --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

Then open in browser: [https://127.0.0.1:8000/submit-json/]

---

### Run the Worker

```bash
python worker.py runserver

```

---

## 📝 JSON Job Format (Toy Example)

```json
{
  "a": 3,
  "b": 2
}
```

If fields `a` and `b` are missing, defaults are used: `a=1`, `b=0`

---

## ⚠️ Known Limitations

* Current backend **ignores complex JSON job structures** (e.g., nested `job_steps`).
* No JSON schema validation yet.
* Worker simulates job processing via `sleep(a)` instead of real spike sorting.

---

## 📌 Future Improvements

* Parse `a` dynamically from nested JSON fields
* Add JSON schema validation using `jsonschema`
* Support DAG-style job execution (based on `job_steps` and dependencies)
* NAS integration for file persistence
* Real spike sorting using SpikeInterface

---

## 📚 Acknowledgements

Built in the Laboratory of Systems Neural Development at George Washington University. This toy system is designed to explore secure job queuing, API-driven worker orchestration, and spike sorting pipeline foundations.

---


#Token needs to be paste in dev consol 
localStorage.setItem('token','7dad800f91999d083ee56e6d2e59c87a3f43a0df')