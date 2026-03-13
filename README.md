# Spike Sorting Lab Hub

A spike sorting job management system built with Django + React. Allows researchers to submit spike sorting pipelines via JSON, track job progress in real-time, and manage job statuses.

## Tech Stack

- **Backend:** Django 4.2.7 + Django REST Framework
- **Frontend:** React 18
- **Database:** SQLite / PostgreSQL
- **Authentication:** Token-based (DRF)
- **Worker:** Python polling consumer

## Key Features

- End-to-end job creation with atomic transactions
- SHA-256 configuration deduplication
- Pipeline dependency resolution
- Real-time status updates via React UI
- Admin interface for manual control
- FIFO queue with row-level database locking

## Setup & Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL or SQLite

### Install

```bash
# Clone and enter project
git clone <repo-url>
cd spikesorting-labhub-try-error

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Frontend
cd my-app
npm install
npm run build
cd ..

# Run
python manage.py runserver
```

### Environment Variables

```bash
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://...
```

## API Reference

All endpoints require token authentication:

```
Authorization: Token YOUR_TOKEN_HERE
```

**Get Token:**
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs/create-sorting-job/` | Create a new job |
| GET | `/jobs/list/` | List all jobs (supports `status`, `limit`, `offset`) |
| GET | `/jobs/status/<job_id>/` | Get job details and step statuses |
| GET | `/jobs/statistics/` | Job count breakdown by status |
| GET | `/qmodel/getthenextjob/` | Worker: fetch next pending job |
| POST | `/qmodel/getthenextjob/` | Worker: update job or step status |

### Create Job Example

```bash
curl -X POST http://localhost:8000/jobs/create-sorting-job/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recording": {
      "binfile": "/data/recording.bin",
      "sampling_rate": 30000,
      "num_channels": 32,
      "gain": 0.195,
      "offset": 0,
      "probe": "/data/probe.json"
    },
    "pipeline_id": 1,
    "environment": "local"
  }'
```

## Status Flow

```
Job:  pending -> fetched -> running -> finished
                                    -> failed

Step: pending -> running -> completed
                          -> failed
```

## Project Structure

```
labhub/          # Django project settings
qmodel/          # Core models, worker endpoints, admin
  models.py      # Job, JobStep, StepConfig, pure functions
  views.py       # Worker GET/POST endpoints
  admin.py       # Admin actions for status management
jobs/            # Job creation API
  views.py       # create_sorting_job, list_jobs, statistics
  serializers.py # CreateSortingJobSerializer
my-app/          # React frontend
```

## Running Tests

```bash
python manage.py test qmodel -v 2
```

## Admin Interface

Access at `http://localhost:8000/admin/` to manually update job and step statuses.

## Web Interface

Access at `http://localhost:8000/` to view jobs, track progress, and update statuses via the React UI.

## Production Deployment

```bash
# Prepare
python manage.py check
python manage.py collectstatic --noinput

# Required settings
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Deploy with Gunicorn behind Nginx (recommended for SSL termination).

## Common Issues

| Issue | Fix |
|-------|-----|
| Token invalid | Create new token via admin or shell |
| Job not processing | Check worker is running |
| Step status not updating | Verify status choices in model (`completed`, not `finished`) |
| Dependencies broken | Check `depends_on` contains real `config_block_hash` values |
| Deduplication not working | Ensure `compute_fingerprint()` uses `sort_keys=True` |
