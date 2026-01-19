# End-to-End Job Submission - Complete Test Flow

## What Was Fixed

### 1. **Endpoint URL**
- ❌ Was: `/qmodel/jobs/create/`
- ✅ Now: `/jobs/create/`

### 2. **Payload Structure**
React now sends the correct format:
```javascript
{
  "pipeline_id": 2,
  "recording_config": {
    "binfile": "/path/to/file.dat",
    "sampling_rate": 30000.0,
    "number_of_channels": 256,
    "gain_to_uV": 0.195,
    "offset_to_uV": 0.0,
    "probe": "/path/to/probe.json",
    "bad_channels": [130, 131, 140]
  },
  "job_env_preset": {
    "base_directory": "$LOCAL$/random_uuid",
    "job_kwargs": {
      "n_jobs": 40,
      "total_memory": "128G",
      "chunk_duration": "60s",
      "progress_bar": true
    },
    "log_level": "DEBUG",
    "REDIRECT": {
      "log": "$NAS$/__RECORDING_DIRECTORY__/uuid/run.log",
      "out": "$NAS$/__RECORDING_DIRECTORY__/uuid/run.out",
      "err": "$NAS$/__RECORDING_DIRECTORY__/uuid/run.err"
    }
  }
}
```

### 3. **Dependency Resolution**
- ❌ Was: Hardcoded logic for each step type
- ✅ Now: Uses STEP_DEPENDENCIES specification from `jobs/step_config.py`

The new system properly handles:
- Recording: `depends_on: []` (no dependencies)
- Preprocessing: depends on recording
- Sorting: depends on preprocessing
- Analyzer: depends on preprocessing AND sorting
- Phy_export: depends on preprocessing AND sorting
- Upload: depends on analyzer and/or phy_export

### 4. **Pipeline Model**
Updated `PipelineStep` model to include:
- `order` - Execution order
- `function` - Step function name
- `config` - Step configuration

## Complete End-to-End Flow

### Frontend (React - my-app/)
```
User fills wizard:
├─ Step 1: Recording Configuration
│  ├─ Upload bin file (stored as File object)
│  ├─ Upload probe file (stored as File object)
│  ├─ Enter sampling rate, channels, gain, offset
│  └─ Mark bad channels
│
├─ Step 2: Select Pipeline
│  └─ Fetch from /pipeline/pipelines/ API
│
├─ Step 3: Select Environment
│  └─ Choose preset (default)
│
└─ Step 4: Review & Submit
   └─ POST to /jobs/create/ with payload
```

### Backend (Django - jobs app)
```
jobs/views.py create_job():

1. VALIDATE:
   - pipeline_id exists
   - recording_config provided
   - job_env_preset provided

2. ATOMIC TRANSACTION:
   ├─ STEP 1: Create Job
   │  └─ job = Job.objects.create(job_env_config=job_env_preset)
   │
   ├─ STEP 2: Create recording StepConfig
   │  └─ recording_hash = get_or_create_step_configs("recording", config)
   │
   ├─ STEP 3: Create recording JobStep
   │  └─ JobStep.objects.create(
   │       identifier=recording_hash,
   │       depends_on=[],
   │       function="recording"
   │     )
   │
   ├─ STEP 4: Fetch pipeline steps
   │  └─ PipelineStep.objects.filter(pipeline=pipeline).order_by('order')
   │
   ├─ STEPS 5-8: For each pipeline step:
   │  ├─ Create StepConfig (deduped by SHA-256 hash)
   │  ├─ Look up STEP_DEPENDENCIES spec
   │  ├─ Find dependencies from previous steps matching spec
   │  └─ Create JobStep with proper depends_on
   │
   └─ STEP 9: Commit + Log success

3. RETURN:
   {
     "message": "Job created successfully",
     "job_id": "f34fead1-de24-4447-82cf-5c40160ec80b",
     "job": {
       "job_id": "...",
       "status": "pending",
       "steps": [...]
     }
   }
```

## Database State After Submission

### Job Table
```
job_id                 | status  | created_at
f34fead1-de24-4447...  | pending | 2026-01-19 10:00:00
```

### StepConfig Table
```
config_block_hash | function      | config (JSON)
7ea0910ccea1      | recording     | {...}
754fed717d11      | preprocessing | {...}
876194051d93      | sorting       | {...}
a12959d82f54      | analyzer      | {...}
500373039381      | phy_export    | {...}
dadb9f1689be      | upload        | {...}
```

### JobStep Table
```
job_id | identifier    | function      | status  | depends_on
...    | 7ea0910ccea1  | recording     | pending | []
...    | 754fed717d11  | preprocessing | pending | ["7ea0910ccea1"]
...    | 876194051d93  | sorting       | pending | ["754fed717d11"]
...    | a12959d82f54  | analyzer      | pending | ["754fed717d11", "876194051d93"]
...    | 500373039381  | phy_export    | pending | ["754fed717d11", "876194051d93"]
...    | dadb9f1689be  | upload        | pending | ["a12959d82f54", "500373039381"]
```

### JobCreationLog Table
```
job_id | pipeline_id | status  | created_at
...    | 2           | success | 2026-01-19 10:00:00
```

## Testing Steps

### Prerequisites
1. Django server running: `python manage.py runserver`
2. Token obtained from login
3. Pipeline created (ID 2 exists)

### Test 1: Simple Job Creation via React UI
1. Open http://localhost:8000/
2. Login with credentials
3. Click "Create Sorting Job"
4. Fill Step 1: Recording (use dummy values)
5. Fill Step 2: Select pipeline ID 2
6. Fill Step 3: Environment preset
7. Review Step 4
8. Click Submit
9. Check browser console for POST request to `/jobs/create/`
10. Verify success response with job_id

### Test 2: Direct API Call
```bash
TOKEN="your_token_here"
curl -X POST http://localhost:8000/jobs/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{
    "pipeline_id": 2,
    "recording_config": {
      "binfile": "/local/rth/recording.dat",
      "sampling_rate": 30000.0,
      "number_of_channels": 256,
      "gain_to_uV": 0.195,
      "offset_to_uV": 0.0,
      "probe": "/local/probes/probe.json",
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
        "log": "$NAS$/__RECORDING_DIRECTORY__/test_job/run.log",
        "out": "$NAS$/__RECORDING_DIRECTORY__/test_job/run.out",
        "err": "$NAS$/__RECORDING_DIRECTORY__/test_job/run.err"
      }
    }
  }'
```

### Test 3: Verify Database State
```bash
# Check job was created
sqlite3 db.sqlite3 "SELECT job_id, status FROM qmodel_job ORDER BY created_at DESC LIMIT 1;"

# Check all JobSteps
sqlite3 db.sqlite3 "SELECT job_id, function, depends_on FROM qmodel_jobstep ORDER BY created_at;"

# Check JobCreationLog
sqlite3 db.sqlite3 "SELECT job_id, pipeline_id, status FROM jobs_jobcreationlog ORDER BY created_at DESC LIMIT 1;"
```

### Test 4: Get Job Status
```bash
TOKEN="your_token_here"
JOB_ID="f34fead1-de24-4447-82cf-5c40160ec80b"
curl http://localhost:8000/jobs/status/$JOB_ID/ \
  -H "Authorization: Token $TOKEN"
```

## Key Improvements

✅ **Uses Specification** - Dependency logic from STEP_DEPENDENCIES
✅ **Proper Field Mapping** - React fields correctly mapped to backend schema
✅ **Atomic Transactions** - All-or-nothing job creation
✅ **Error Handling** - Comprehensive validation and error messages
✅ **Audit Logging** - All attempts logged in JobCreationLog
✅ **RESTful API** - Proper HTTP methods and status codes
✅ **Authentication** - Token-based security

## Files Changed

1. `my-app/src/pages/wizard-steps/StepReview.js` - Updated endpoint and payload
2. `jobs/views.py` - Fixed pipeline lookup, added step_config import
3. `jobs/step_config.py` - New file with STEP_DEPENDENCIES
4. `pipeline/models.py` - Added order, function, config fields to PipelineStep
5. `my-app/build/` - Rebuilt with fixed submission logic

## Next Steps

1. **Test end-to-end with real pipeline**
   - Ensure PipelineSteps are properly configured with function and config
   - Verify dependencies resolve correctly

2. **Update Worker** (`qmodel_worker.py`)
   - Read from new Job/JobStep models
   - Respect dependency ordering
   - Update job status to "running", "finished", or "failed"

3. **Add Status Polling**
   - Frontend polls `/jobs/status/<job_id>/` for updates
   - Show progress and errors

4. **Error Handling**
   - Handle missing PipelineSteps
   - Handle invalid function names
   - Handle dependency resolution failures
