#!/bin/bash

# Simple End-to-End Workflow Test
# Tests job submission and worker API without the web form

set -e

echo "🚀 Simple QModel Workflow Test"
echo "=============================="

cd /Users/kajalpatel/spikesorting-labhub-try-error
VENV_PYTHON="/Users/kajalpatel/spikesorting-labhub-try-error/.venv/bin/python"
BASE_URL="https://localhost"

# Step 1: Create test user and get token
echo "👤 Setting up authentication..."
AUTH_TOKEN=$($VENV_PYTHON manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create or get user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com', 'is_superuser': True, 'is_staff': True}
)
if created:
    user.set_password('testpass123')
    user.save()

# Get or create token
token, created = Token.objects.get_or_create(user=user)
print(token.key)
" 2>/dev/null | tail -1)

echo "🔑 Token: ${AUTH_TOKEN:0:10}..."

# Step 2: Create job directly in database
echo "📝 Creating test job in database..."
$VENV_PYTHON manage.py shell -c "
from qmodel.models import Job, JobStep, StepConfig
import json

# Create job
job = Job.objects.create(
    identifier='test_workflow_simple',
    job_env_config={'test': 'true', 'environment': 'test'},
    status='pending'
)

print(f'Job created: {job.job_id}')

# Create step config
config1 = {'input_file': '/tmp/test.txt', 'output_file': '/tmp/result.txt'}
config2 = {'threshold': 0.05, 'method': 'correlation'}

step_config1, created = StepConfig.objects.get_or_create(
    config_block_hash='hash1',
    defaults={'config_block': config1}
)

step_config2, created = StepConfig.objects.get_or_create(
    config_block_hash='hash2', 
    defaults={'config_block': config2}
)

# Create job steps
JobStep.objects.create(
    identifier='preprocess',
    job=job,
    function='preprocess_data',
    depends_on=[],
    config_block_hash=step_config1,
    status='pending'
)

JobStep.objects.create(
    identifier='analyze',
    job=job,
    function='analyze_data', 
    depends_on=['preprocess'],
    config_block_hash=step_config2,
    status='pending'
)

print(f'Job steps created: {job.jobstep_set.count()}')
"

# Step 3: Test worker API
echo "🤖 Testing worker API..."
WORKER_RESPONSE=$(curl -s -k -H "Authorization: Token $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    "$BASE_URL/qmodel/getthenextjob/" \
    -w "\n%{http_code}")

echo "Worker API Response:"
echo "$WORKER_RESPONSE"

# Step 4: Check database state
echo "🗄️ Checking database state..."
$VENV_PYTHON manage.py shell -c "
from qmodel.models import Job, JobStep

job = Job.objects.filter(identifier='test_workflow_simple').first()
if job:
    print(f'=== Job Status ===')
    print(f'ID: {job.job_id}')
    print(f'Identifier: {job.identifier}')
    print(f'Status: {job.status}')
    print(f'Created: {job.created_at}')
    print(f'')
    
    steps = job.jobstep_set.all()
    print(f'=== Steps ({steps.count()}) ===')
    for step in steps:
        print(f'{step.identifier}: {step.status} ({step.function})')
        print(f'  Depends on: {step.depends_on}')
        print(f'  Config: {step.config_block_hash.config_block}')
        print('')
        
    print(f'=== Summary ===') 
    print(f'Total Jobs: {Job.objects.count()}')
    print(f'Total Steps: {JobStep.objects.count()}')
else:
    print('❌ Job not found!')
"

# Step 5: Test status update API
echo "🔄 Testing status update..."
JOB_ID=$($VENV_PYTHON manage.py shell -c "
from qmodel.models import Job
job = Job.objects.filter(identifier='test_workflow_simple').first()
if job:
    print(job.job_id)
" 2>/dev/null | tail -1)

if [ ! -z "$JOB_ID" ]; then
    UPDATE_RESPONSE=$(curl -s -k -X POST \
        -H "Authorization: Token $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"job_id\": \"$JOB_ID\", \"status\": \"running\"}" \
        "$BASE_URL/qmodel/getthenextjob/" \
        -w "\n%{http_code}")
    
    echo "Status update response:"
    echo "$UPDATE_RESPONSE"
fi

# Step 6: Final verification
echo "✅ Final verification..."
$VENV_PYTHON manage.py shell -c "
from qmodel.models import Job

job = Job.objects.filter(identifier='test_workflow_simple').first()
if job:
    print(f'Final job status: {job.status}')
    print(f'Last updated: {job.updated_at}')
else:
    print('Job not found')
"

echo ""
echo "🎉 Simple Workflow Test Complete!"
echo "================================="
