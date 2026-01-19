# Jobs App Implementation - Testing Guide

## Overview
The new `jobs` app implements the complete job creation workflow with proper dependency injection and step-by-step execution.

## Architecture

### Apps Structure
```
- qmodel/ (existing) - StepConfig, Job, JobStep models + utility functions
- pipeline/ (existing) - Pipeline and PipelineStep models
- jobs/ (new) - Job creation views, serializers, and logging
```

### Models

#### JobCreationLog (jobs/models.py)
- Tracks all job creation requests
- Logs success/failure with error messages
- Audit trail for debugging

#### Job, JobStep, StepConfig (in qmodel/models.py)
- Already exist with proper relationships
- Used by jobs app for job creation

## API Endpoints

### 1. Create Job
**Endpoint:** `POST /jobs/create/`

**Request Body:**
```json
{
  "pipeline_id": 2,
  "recording_config": {
    "binfile": "/path/to/data.dat",
    "sampling_rate": 30000.0,
    "number_of_channels": 256,
    "gain_to_uV": 0.195,
    "offset_to_uV": 0.0,
    "probe": "/path/to/probe.json",
    "bad_channels": [130, 131, 140, 211, 255]
  },
  "job_env_preset": {
    "base_directory": "$LOCAL$/job_123",
    "job_kwargs": {
      "n_jobs": 40,
      "total_memory": "128G",
      "chunk_duration": "60s",
      "progress_bar": true
    },
    "log_level": "DEBUG",
    "REDIRECT": {
      "log": "$NAS$/__RECORDING_DIRECTORY__/run.log",
      "out": "$NAS$/__RECORDING_DIRECTORY__/run.out",
      "err": "$NAS$/__RECORDING_DIRECTORY__/run.err"
    }
  }
}
```

**Response (201 Created):**
```json
{
  "message": "Job created successfully",
  "job_id": "f34fead1-de24-4447-82cf-5c40160ec80b",
  "job": {
    "job_id": "f34fead1-de24-4447-82cf-5c40160ec80b",
    "status": "pending",
    "created_at": "2026-01-19T09:53:00Z",
    "job_env_config": {...},
    "steps": [
      {
        "identifier": "7ea0910ccea1",
        "function": "recording",
        "status": "pending",
        "depends_on": [],
        "config": {...}
      },
      {
        "identifier": "754fed717d11",
        "function": "preprocessing",
        "status": "pending",
        "depends_on": ["7ea0910ccea1"],
        "config": {...}
      },
      ...
    ]
  }
}
```

### 2. Get Job Status
**Endpoint:** `GET /jobs/status/<job_id>/`

**Response (200 OK):**
```json
{
  "job_id": "f34fead1-de24-4447-82cf-5c40160ec80b",
  "status": "pending",
  "created_at": "2026-01-19T09:53:00Z",
  "job_env_config": {...},
  "steps": [...]
}
```

### 3. Get All Jobs
**Endpoint:** `GET /jobs/` or `GET /jobs/?status=pending`

**Query Parameters:**
- `status` (optional) - Filter by status: pending, fetched, running, finished, failed

**Response (200 OK):**
```json
[
  {
    "job_id": "f34fead1-de24-4447-82cf-5c40160ec80b",
    "status": "pending",
    ...
  },
  ...
]
```

## Step-by-Step Job Creation Flow

### Inside `create_job()` View (Single Transaction)

```
STEP 0: Receive single POST request with:
  - pipeline_id
  - recording_config
  - job_env_preset

STEP 1: Create Job row
  - job = Job.objects.create(job_env_config=job_env_preset, status="pending")
  - Now have job.job_id

STEP 2: Create recording StepConfig
  - recording_hash = get_or_create_step_configs("recording", recording_config)
  - This returns the SHA-256 hash of the config

STEP 3: Create recording JobStep
  - JobStep.objects.create(
      job=job,
      identifier=recording_hash,
      function="recording",
      depends_on=[],  # No dependencies
      config_block_hash_id=recording_hash,
      status="pending"
    )

STEP 4: Fetch pipeline structure
  - pipeline_steps = PipelineStep.objects.filter(pipeline=pipeline).order_by('order')

STEP 5-8: For each pipeline step (preprocessing, sorting, analyzer, phy_export, upload):
  - Create StepConfig for this function
  - Determine dependencies based on step type:
    * preprocessing → depends_on=[recording_hash]
    * sorting → depends_on=[preprocessing_hash]
    * analyzer → depends_on=[preprocessing_hash, sorting_hash]
    * phy_export → depends_on=[preprocessing_hash, sorting_hash]
    * upload → depends_on=[analyzer_hash, phy_export_hash]
  - Create JobStep with injected dependencies

STEP 9: Commit transaction
  - All DB changes committed atomically
  - Log job creation in JobCreationLog
  - Return success response
```

## Testing Workflow

### Prerequisites
1. Django server running: `python manage.py runserver`
2. You must be logged in or have valid token
3. Pipeline must exist in database

### Test Using cURL

```bash
# Create job
curl -X POST http://localhost:8000/jobs/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "pipeline_id": 2,
    "recording_config": {
      "binfile": "/path/to/data.dat",
      "sampling_rate": 30000.0,
      "number_of_channels": 256,
      "gain_to_uV": 0.195,
      "offset_to_uV": 0.0,
      "probe": "/path/to/probe.json",
      "bad_channels": [130, 131]
    },
    "job_env_preset": {
      "base_directory": "$LOCAL$/test_job",
      "job_kwargs": {
        "n_jobs": 40,
        "total_memory": "128G",
        "chunk_duration": "60s",
        "progress_bar": true
      },
      "log_level": "DEBUG",
      "REDIRECT": {
        "log": "/tmp/test_job/run.log",
        "out": "/tmp/test_job/run.out",
        "err": "/tmp/test_job/run.err"
      }
    }
  }'

# Get job status
curl http://localhost:8000/jobs/status/f34fead1-de24-4447-82cf-5c40160ec80b/ \
  -H "Authorization: Token YOUR_TOKEN"

# Get all jobs
curl http://localhost:8000/jobs/ \
  -H "Authorization: Token YOUR_TOKEN"

# Filter by status
curl "http://localhost:8000/jobs/?status=pending" \
  -H "Authorization: Token YOUR_TOKEN"
```

## Database Schema

### JobCreationLog Table
- `id` (Primary Key)
- `job` (Foreign Key to Job) - Optional (NULL if job creation failed)
- `pipeline_id` (Integer)
- `recording_config` (JSON)
- `job_env_preset` (JSON)
- `created_at` (DateTime)
- `status` (CharField: pending, success, failed)
- `error_message` (TextField) - Only if failed

### Related Tables (qmodel app)
- `Job` - Main job record with UUID primary key
- `JobStep` - Individual steps with depends_on array
- `StepConfig` - Unique configs with SHA-256 hash as key

## Key Features

✅ **Atomic Transactions** - All steps created together or none at all
✅ **Dependency Injection** - Each step knows its dependencies from pipeline
✅ **Config Deduplication** - Same configs reused via SHA-256 hashing
✅ **Audit Logging** - All job creation attempts logged
✅ **Error Handling** - Comprehensive error messages and logging
✅ **Authentication** - Token-based authentication required
✅ **Proper Serialization** - Nested serializers for complex data

## Files Created

1. `jobs/models.py` - JobCreationLog model
2. `jobs/serializers.py` - Serializers for Job, JobStep, StepConfig, JobCreationLog
3. `jobs/views.py` - Job creation, status, and list views
4. `jobs/urls.py` - URL routing
5. `jobs/admin.py` - Django admin integration
6. `jobs/migrations/0001_initial.py` - Database migration
7. `jobs/apps.py` - App configuration (auto-generated)

## Configuration Changes

1. `labhub/settings.py` - Added `jobs` to INSTALLED_APPS
2. `labhub/urls.py` - Added jobs URL routing and updated regex pattern
