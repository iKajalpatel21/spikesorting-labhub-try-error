#!/bin/bash

# Complete End-to-End Workflow Test
# Tests the entire pipeline: JSON upload → Server → Worker → Database verification

set -e  # Exit on any error

echo "🚀 Starting Complete End-to-End Workflow Test"
echo "=============================================="

# Configuration
BASE_URL="https://localhost"
DJANGO_SUPERUSER_USERNAME="testuser"
DJANGO_SUPERUSER_PASSWORD="testpass123"
DJANGO_SUPERUSER_EMAIL="test@example.com"
TEST_JSON_FILE="/tmp/test_job.json"

# Create test JSON file
echo "📝 Creating test job JSON file..."
cat > "$TEST_JSON_FILE" << 'EOF'
{
  "job_evn": {
    "identifier": "test_job_e2e_001",
    "env_variable_1": "value1",
    "env_variable_2": "value2"
  },
  "job_steps": [
    {
      "identifier": "step1",
      "function": "preprocess_data",
      "depends": []
    },
    {
      "identifier": "step2", 
      "function": "analyze_data",
      "depends": ["step1"]
    }
  ],
  "step1": {
    "input_file": "/path/to/input.txt",
    "output_file": "/path/to/output.txt",
    "parameter1": "value1"
  },
  "step2": {
    "analysis_type": "correlation",
    "threshold": 0.05,
    "parameter2": "value2"
  }
}
EOF

echo "✅ Test JSON file created: $TEST_JSON_FILE"

# Function to check service status
check_service_status() {
    local service_name=$1
    if pgrep -f "$service_name" > /dev/null; then
        echo "✅ $service_name is running"
        return 0
    else
        echo "❌ $service_name is not running"
        return 1
    fi
}

# Check if all services are running
echo "🔍 Checking service status..."
check_service_status "nginx" || (echo "Please start nginx first" && exit 1)
check_service_status "gunicorn" || (echo "Please start gunicorn first" && exit 1)

# Step 1: Create Django superuser if doesn't exist
echo "👤 Setting up Django superuser..."
cd /Users/kajalpatel/spikesorting-labhub-try-error

# Use virtual environment Python
VENV_PYTHON="/Users/kajalpatel/spikesorting-labhub-try-error/.venv/bin/python"

$VENV_PYTHON manage.py shell << EOF
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create superuser if doesn't exist
try:
    user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
    print("User already exists")
except User.DoesNotExist:
    user = User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD'
    )
    print("Superuser created")

# Get or create token
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
EOF

# Extract the token
AUTH_TOKEN=$($VENV_PYTHON manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
token = Token.objects.get(user=user)
print(token.key)
")

echo "🔑 Authentication token obtained: ${AUTH_TOKEN:0:10}..."

# Step 2: Submit job via file upload API
echo "📤 Submitting job via web interface..."

# Get CSRF token first
CSRF_TOKEN=$(curl -s -k -c /tmp/cookies.txt "$BASE_URL/qmodel/submit-json/" | grep -o 'name="csrfmiddlewaretoken" value="[^"]*"' | cut -d'"' -f4)

if [ -z "$CSRF_TOKEN" ]; then
    echo "❌ Failed to get CSRF token"
    exit 1
fi

echo "🔒 CSRF Token obtained: ${CSRF_TOKEN:0:10}..."

# Submit the job via form upload
SUBMIT_RESPONSE=$(curl -s -k -b /tmp/cookies.txt \
    -F "csrfmiddlewaretoken=$CSRF_TOKEN" \
    -F "json_file=@$TEST_JSON_FILE" \
    "$BASE_URL/qmodel/submit-json/" \
    -w "%{http_code}")

echo "📋 Job submission response code: $SUBMIT_RESPONSE"

# Step 3: Verify job was created in database
echo "🗄️ Verifying job in database..."
JOB_CHECK=$($VENV_PYTHON manage.py shell -c "
from qmodel.models import Job
jobs = Job.objects.filter(identifier='test_job_e2e_001')
if jobs.exists():
    job = jobs.first()
    print(f'Job found: ID={job.job_id}, identifier={job.identifier}, status={job.status}')
    print(f'Job UUID: {job.job_id}')
else:
    print('No job found with identifier test_job_e2e_001')
    # List all jobs
    all_jobs = Job.objects.all()
    print(f'Total jobs in database: {all_jobs.count()}')
    for job in all_jobs:
        print(f'  - ID={job.job_id}, identifier={job.identifier}, status={job.status}')
")

echo "$JOB_CHECK"

# Step 4: Test worker API endpoint
echo "🤖 Testing worker API (get next job)..."
WORKER_RESPONSE=$(curl -s -k -H "Authorization: Token $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    "$BASE_URL/api/jobs/get_next_job/" \
    -w "\n%{http_code}")

echo "Worker API Response:"
echo "$WORKER_RESPONSE"

# Step 5: Check if job status changed
echo "🔄 Checking job status after worker fetch..."
STATUS_CHECK=$($VENV_PYTHON manage.py shell -c "
from qmodel.models import Job
jobs = Job.objects.filter(identifier='test_job_e2e_001')
if jobs.exists():
    job = jobs.first()
    print(f'Job status: {job.status}')
    # Also check job steps
    steps = job.jobstep_set.all()
    print(f'Job steps count: {steps.count()}')
    for step in steps:
        print(f'  - Step: {step.identifier}, function: {step.function}, status: {step.status}')
else:
    print('Job not found')
")

echo "$STATUS_CHECK"

# Step 6: Simulate worker processing
echo "⚙️ Simulating worker processing..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="$VENV_PYTHON"
fi

# Run worker once to process the job
echo "🔧 Running worker to process job..."
timeout 30s $VENV_PYTHON qmodel_worker_production.py || true

# Step 7: Final verification
echo "✅ Final verification..."
FINAL_CHECK=$($VENV_PYTHON manage.py shell -c "
from qmodel.models import Job, JobStep
jobs = Job.objects.filter(identifier='test_job_e2e_001')
if jobs.exists():
    job = jobs.first()
    print(f'=== Final Job Status ===')
    print(f'Job ID: {job.job_id}')
    print(f'Identifier: {job.identifier}')
    print(f'Status: {job.status}')
    print(f'Created: {job.created_at}')
    print(f'Updated: {job.updated_at}')
    print(f'')
    
    steps = job.jobstep_set.all()
    print(f'=== Job Steps ({steps.count()}) ===')
    for step in steps:
        print(f'Step: {step.identifier}')
        print(f'  Function: {step.function}')
        print(f'  Status: {step.status}')
        print(f'  Depends on: {step.depends_on}')
        print(f'')
    
    print(f'=== Summary ===')
    print(f'Total Jobs: {Job.objects.count()}')
    print(f'Total Steps: {JobStep.objects.count()}')
else:
    print('❌ Job not found in final check')
")

echo "$FINAL_CHECK"

# Cleanup
echo "🧹 Cleaning up..."
rm -f "$TEST_JSON_FILE" /tmp/cookies.txt

echo ""
echo "🎉 End-to-End Workflow Test Complete!"
echo "====================================="
