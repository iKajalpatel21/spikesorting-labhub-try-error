# Testing Job Creation Flow

## Quick Test (Without UI)

### 1. Get a login token
```bash
curl -X POST http://127.0.0.1:8000/qmodel/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

Response:
```json
{"token": "YOUR_TOKEN_HERE", "user_id": 1, "username": "admin"}
```

### 2. Create a job
```bash
curl -X POST http://127.0.0.1:8000/qmodel/jobs/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{
    "recording": {
      "samplingRate": 30000,
      "numChannels": 32,
      "gainToMicroVolts": 0.195,
      "offsetToMicroVolts": 0,
      "badChannels": [1, 2]
    },
    "pipeline_id": 1,
    "job_env_preset": "default"
  }'
```

Expected Response (201 Created):
```json
{
  "job_id": "uuid-here",
  "job_env_config": {
    "base_directory": "$LOCAL$/uuid-here",
    "job_kwargs": {...},
    "log_level": "DEBUG",
    "REDIRECT": {...}
  },
  "status": "created"
}
```

## UI Testing

### Step-by-Step:

1. **Login Page**
   - Go to http://localhost:8000/login
   - Username: `admin`
   - Password: `admin`
   - Click "Login"
   - Should redirect to dashboard

2. **Dashboard**
   - You should see 3 cards: "Create Sorting Job", "Add New Pipeline", "Manage Jobs"
   - Click "Create Sorting Job"

3. **Step 1: Recording**
   - Upload a binary file (any file for testing)
   - Upload a probe file (any file for testing)
   - Set parameters:
     - Sampling Rate: 30000
     - Number of Channels: 32
     - Gain to µV: 0.195
     - Offset to µV: 0
   - Optionally select bad channels
   - Click "Next >"

4. **Step 2: Pipeline**
   - A table should appear with 4 pipelines
   - Select one by clicking the checkbox or row
   - Click "Next >"

5. **Step 3: Job Environment**
   - A single checkbox "Default Environment (Recommended)" should appear
   - It should be checked by default
   - Click "Next >"

6. **Step 4: Review & Submit**
   - Review your settings
   - Click "✅ Submit Job"
   - If successful: Alert shows "✅ Job created successfully! Job ID: xxx"
   - If error: Error message appears in red box below the review sections

## Troubleshooting

### Common Issues:

1. **"No authentication token found"**
   - You haven't logged in
   - Go to http://localhost:8000/login and log in

2. **"Pipeline not selected"**
   - Go back to Step 2 (Pipeline) and select a pipeline

3. **"Failed to create job (401)"**
   - Token is invalid
   - Log out and log back in

4. **"Failed to create job (400)"**
   - Check server logs
   - Ensure pipeline_id exists in database (1, 2, 3, or 4)

### Check Console:

Open browser DevTools (F12 or Cmd+Option+I) and go to Console tab to see:
- `console.log` messages showing the payload being sent
- Any fetch errors
- Response status codes

## Database Check

### View Created Jobs:

```bash
python manage.py shell
>>> from qmodel.models import Job
>>> Job.objects.all()
```

### View Available Pipelines:

```bash
curl -X GET http://127.0.0.1:8000/pipeline/pipelines/ \
  -H "Authorization: Token YOUR_TOKEN"
```

Should return array with pipeline_id, description, created_at, step_count, steps[]
