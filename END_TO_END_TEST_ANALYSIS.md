# End-to-End Job Submission Flow - Issues & Solutions

## Current Issues Found

### Issue 1: Wrong API Endpoint
**Location:** StepReview.js line 43
**Current:** `'/qmodel/jobs/create/'`
**Should be:** `'/jobs/create/'`

### Issue 2: Wrong Payload Structure
**Current React sends:**
```javascript
{
  "recording": {
    "samplingRate": 30000,
    "numChannels": 32,
    "gainToMicroVolts": 0.195,
    "offsetToMicroVolts": 0,
    "badChannels": []
  },
  "pipeline_id": 2,
  "job_env_preset": { "preset": "default" }
}
```

**Expected by jobs/views.py (create_job):**
```javascript
{
  "recording_config": {
    "binfile": "/path/to/file.dat",
    "sampling_rate": 30000.0,
    "number_of_channels": 256,
    "gain_to_uV": 0.195,
    "offset_to_uV": 0.0,
    "probe": "/path/to/probe.json",
    "bad_channels": [130, 131, 140]
  },
  "pipeline_id": 2,
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

### Issue 3: Missing Field Mapping
React collects:
- `binFile` (File object) → needs path
- `probeFile` (File object) → needs path
- `samplingRate` → correct but wrong casing
- `numChannels` → needs `number_of_channels`
- `gainToMicroVolts` → needs `gain_to_uV`
- `offsetToMicroVolts` → needs `offset_to_uV`
- `badChannels` → correct but wrong casing

### Issue 4: Missing Job Environment Details
React only stores: `{ preset: "default" }`
Needs full structure with:
- base_directory
- job_kwargs (n_jobs, total_memory, chunk_duration, progress_bar)
- log_level
- REDIRECT (log, out, err paths)

## Step-by-Step Flow Analysis

### Frontend (React)
```
1. User enters recording file info (files + parameters)
2. User selects pipeline
3. User selects environment preset
4. User reviews settings
5. User clicks "Submit Job"
   ↓
   React collects: { recording, selectedPipeline, jobEnvironment }
   ↓
   POST to /jobs/create/ with payload
```

### Backend (Django)
```
1. jobs/views.py create_job() receives request
2. Validates: pipeline_id, recording_config, job_env_preset
3. Transaction starts:
   - Step 1: Create Job
   - Step 2: Create recording StepConfig
   - Step 3: Create recording JobStep (no deps)
   - Step 4: Fetch pipeline templates
   - Step 5-8: Create other steps with dependencies
   - Step 9: Commit + Log
4. Return success with job_id
```

## Required Fixes

### Fix 1: Update StepReview.js endpoint and payload
Change from `/qmodel/jobs/create/` to `/jobs/create/`
Map recording fields correctly:
- samplingRate → sampling_rate
- numChannels → number_of_channels
- gainToMicroVolts → gain_to_uV
- offsetToMicroVolts → offset_to_uV
- badChannels → bad_channels
- Add binfile and probe paths
- Rename "recording" to "recording_config"

### Fix 2: Expand job_env_preset structure
Add full environment configuration:
- base_directory (generate UUID-based)
- job_kwargs with n_jobs, total_memory, chunk_duration, progress_bar
- log_level
- REDIRECT with log, out, err paths

### Fix 3: Update StepEnvironment.js
Currently only stores "preset", needs to generate full config

## Testing Checklist

- [ ] React sends correct endpoint
- [ ] React sends correct field names
- [ ] React sends required fields
- [ ] Backend receives and validates
- [ ] Job created in database
- [ ] JobSteps created with correct dependencies
- [ ] JobCreationLog records success
- [ ] Response returns job_id
