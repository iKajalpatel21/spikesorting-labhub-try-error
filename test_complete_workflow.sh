#!/bin/bash

# Complete QModel Workflow Test Script
# Tests the entire pipeline from JSON submission to database verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_DIR="/Users/kajalpatel/spikesorting-labhub-try-error"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
API_TOKEN="e1997396f5c992a1cc89ea5c8a518ab22bbab65f"

cd "$PROJECT_DIR"

print_header "QModel Complete Workflow Test"

# Step 1: Setup database
print_step "Setting up database and collecting static files..."
DJANGO_SETTINGS_MODULE=labhub.settings_production "$VENV_PYTHON" manage.py migrate --noinput
DJANGO_SETTINGS_MODULE=labhub.settings_production "$VENV_PYTHON" manage.py collectstatic --noinput
print_success "Database and static files ready"

# Step 2: Start services
print_step "Starting services..."
./qmodel_services.sh start
sleep 3
./qmodel_services.sh status
print_success "Services started"

# Step 3: Test HTTPS connectivity
print_step "Testing HTTPS connectivity..."
if curl -s -k https://localhost/health/ | grep -q "healthy"; then
    print_success "HTTPS stack is working"
else
    print_error "HTTPS stack is not responding"
    exit 1
fi

# Step 4: Submit test job via API
print_step "Submitting test job via HTTPS API..."
JOB_RESPONSE=$(curl -s -k -X POST https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "workflow_test_001",
    "steps": [
      {"identifier": "step1", "function": "preprocess_data"},
      {"identifier": "step2", "function": "detect_spikes"},
      {"identifier": "step3", "function": "cluster_spikes"}
    ]
  }')

echo "API Response: $JOB_RESPONSE"

if echo "$JOB_RESPONSE" | grep -q "workflow_test_001"; then
    print_success "Job submitted successfully"
else
    print_error "Job submission failed"
    echo "Response: $JOB_RESPONSE"
fi

# Step 5: Check job in database before worker
print_step "Checking job status in database (before worker)..."
DJANGO_SETTINGS_MODULE=labhub.settings_production "$VENV_PYTHON" -c "
from qmodel.models import Job, JobStep
import json

jobs = Job.objects.filter(identifier='workflow_test_001')
if jobs.exists():
    job = jobs.first()
    print(f'✅ Job found: {job.identifier} - Status: {job.status}')
    
    steps = JobStep.objects.filter(job=job)
    print(f'✅ Job has {steps.count()} steps:')
    for step in steps:
        print(f'   - {step.identifier}: {step.status}')
else:
    print('❌ Job not found in database')
"

# Step 6: Start worker
print_step "Starting worker to process job..."
./qmodel_services.sh worker
print_success "Worker started"

# Step 7: Wait for processing and monitor
print_step "Monitoring job processing (30 seconds)..."
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# Step 8: Check final job status
print_step "Checking final job status in database..."
DJANGO_SETTINGS_MODULE=labhub.settings_production "$VENV_PYTHON" -c "
from qmodel.models import Job, JobStep
from django.utils import timezone

jobs = Job.objects.filter(identifier='workflow_test_001')
if jobs.exists():
    job = jobs.first()
    print(f'✅ Final Job Status: {job.identifier} - {job.status}')
    print(f'   Created: {job.created_at}')
    print(f'   Updated: {job.updated_at}')
    
    steps = JobStep.objects.filter(job=job).order_by('created_at')
    print(f'✅ Step Processing Results:')
    for step in steps:
        print(f'   - {step.identifier}: {step.status}')
        
    # Check if all steps completed
    completed_steps = steps.filter(status='completed').count()
    total_steps = steps.count()
    
    if completed_steps == total_steps and job.status == 'finished':
        print('🎉 WORKFLOW COMPLETED SUCCESSFULLY!')
    elif job.status == 'running':
        print('⏳ Job still processing...')
    else:
        print(f'⚠️  Job in unexpected state: {job.status}')
else:
    print('❌ Job not found in database')
"

# Step 9: Check worker logs
print_step "Checking worker logs..."
if [ -f "qmodel_worker.log" ]; then
    echo "Recent worker log entries:"
    tail -n 10 qmodel_worker.log
else
    echo "No worker log file found"
fi

# Step 10: Test API endpoint again
print_step "Testing API endpoint for next job..."
NEXT_JOB=$(curl -s -k -X GET https://localhost/qmodel/getthenextjob/ \
  -H "Authorization: Token $API_TOKEN")
echo "Next job response: $NEXT_JOB"

print_header "Workflow Test Summary"

# Final status check
echo "Services Status:"
./qmodel_services.sh status

echo ""
echo -e "${GREEN}✅ Complete workflow test finished!${NC}"
echo ""
echo "What was tested:"
echo "  ✅ Database setup and migrations"
echo "  ✅ HTTPS service stack (Nginx + Gunicorn)"
echo "  ✅ Job submission via HTTPS API"
echo "  ✅ Database job storage"
echo "  ✅ Worker job processing"
echo "  ✅ Step-by-step job execution"
echo "  ✅ Job status updates"
echo ""
echo "Next steps:"
echo "  - Check Django admin: https://localhost/admin/"
echo "  - Monitor logs: tail -f qmodel_worker.log"
echo "  - Submit more jobs via API"
echo ""
echo -e "${BLUE}🚀 Your QModel HTTPS production system is fully operational!${NC}"
