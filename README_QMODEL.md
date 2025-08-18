# QModel - Django Job Queue System

A Django-based job queue system with REST API for managing and processing jobs with multiple steps.

## Features

- **Job Queue Management**: Submit, track, and process jobs with multiple steps
- **REST API**: Token-based authentication for secure API access
- **Worker System**: Background worker to process jobs automatically
- **Status Tracking**: Real-time job and step status updates
- **PostgreSQL Support**: Production-ready database configuration

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/iKajalpatel21/spikesorting-labhub-try-error.git
cd spikesorting-labhub-try-error
git checkout qmodel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Configure PostgreSQL (recommended) or use SQLite for development
# Update DATABASES in labhub/settings.py

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create API token
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from rest_framework.authtoken.models import Token
>>> user = User.objects.get(username='your_username')
>>> token = Token.objects.create(user=user)
>>> print(f"Token: {token.key}")
```

### 3. Run the System

```bash
# Start Django server
python manage.py runserver

# In another terminal, start the worker
python qmodel_worker.py
```

## API Endpoints

### Get Next Job (Worker Endpoint)
- **GET** `/qmodel/getthenextjob/`
- **POST** `/qmodel/getthenextjob/` (for status updates)

**Authentication**: Token-based (include `Authorization: Token <your-token>` header)

### Example API Usage

```python
import requests

headers = {'Authorization': 'Token your-token-here'}

# Get next job
response = requests.get('http://localhost:8000/qmodel/getthenextjob/', headers=headers)
job_data = response.json()

# Update job status
payload = {'job_id': 'job-uuid', 'status': 'running'}
requests.post('http://localhost:8000/qmodel/getthenextjob/', json=payload, headers=headers)

# Update step status
payload = {'job_id': 'job-uuid', 'step_id': 'step-id', 'status': 'completed'}
requests.post('http://localhost:8000/qmodel/getthenextjob/', json=payload, headers=headers)
```

## Worker Configuration

The worker (`qmodel_worker.py`) can be configured via environment variables or by editing the script:

```python
# Worker settings in qmodel_worker.py
API_URL = "http://localhost:8000/qmodel/getthenextjob/"
TOKEN = "your-token-here"
POLLING_INTERVAL_SECONDS = 5
```

## Project Structure

```
qmodel/                 # Django app for job queue
├── models.py          # Job, JobStep, StepConfig models
├── views.py           # API views
├── urls.py            # URL routing
├── admin.py           # Django admin interface
└── serializers.py     # DRF serializers

qmodel_worker.py       # Background worker script
labhub/               # Django project settings
├── settings.py       # Main settings
├── urls.py           # Root URL configuration
└── wsgi.py           # WSGI configuration

manage.py             # Django management script
requirements.txt      # Python dependencies
```

## Database Models

### Job
- `id` (UUID): Unique job identifier
- `status`: Current job status (pending, fetched, running, finished, failed)
- `env_config`: JSON field for environment configuration
- `created_at`: Job creation timestamp

### JobStep
- `id` (UUID): Unique step identifier
- `job`: Foreign key to Job
- `step_order`: Step execution order
- `identifier`: Step identifier string
- `function`: Function name to execute
- `depends_on`: Dependencies (JSON field)
- `status`: Step status
- `config`: Step configuration (JSON field)

### StepConfig
- `id`: Auto-increment primary key
- `step`: Foreign key to JobStep
- `config_block`: JSON configuration data

## Development

### Running Tests
```bash
python manage.py test
```

### Database Migrations
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Admin Interface
Access the Django admin at `http://localhost:8000/admin/` to manage jobs and monitor the queue.

## API Token Setup

1. Create a superuser: `python manage.py createsuperuser`
2. In Django shell, create a token:
```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='your_username')
token = Token.objects.create(user=user)
print(f"Token: {token.key}")
```
3. Use this token in the worker configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
