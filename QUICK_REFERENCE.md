# QModel Clean Architecture - Quick Reference

## 🎯 What Changed?

### Views (Before → After)

**BEFORE:**
```python
@csrf_exempt
def submit_nested_json_job(request):
    # 80+ lines mixing:
    # - JSON file parsing
    # - Manual validation
    # - Business logic
    # - Response handling
    # ❌ REMOVED
```

**AFTER:**
```python
class JobViewSet(viewsets.ModelViewSet):
    # REST CRUD endpoints
    # POST /qmodel/jobs/ ← React submits here

@api_view(["GET", "POST"])
def get_next_job(request):
    # GET: Worker fetches job
    # POST: Worker updates status
```

---

## 📊 Managers (New)

Three pure functions:

```python
# 1. Fingerprint generation
compute_fingerprint(config_block) → str

# 2. Config management
get_or_create_step_configs(data, job_steps) → Dict[str, str]

# 3. Job creation (orchestrator)
create_job_from_payload(payload_data) → Job
```

---

## 🔗 Data Flow

### Job Creation (React → Backend)

```
1. React collects job data
2. POST /qmodel/jobs/ with JSON
3. JobViewSet.create() receives request
4. JobCreationPayloadSerializer validates
5. create_job_from_payload() executes:
   - get_or_create_step_configs() (deduplication)
   - Job.objects.create()
   - JobStep.objects.bulk_create()
6. Return job_id to React
```

### Job Processing (Worker)

```
1. GET /qmodel/getthenextjob/
2. get_next_job() returns pending job
3. Worker processes job
4. POST /qmodel/getthenextjob/ with status update
5. get_next_job() updates status
6. Repeat for next job
```

---

## 📁 Files You Need to Know

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `views.py` | API endpoints | ~50 | ✅ Clean |
| `managers.py` | Business logic | ~150 | ✅ New |
| `serializers.py` | Validation | ~40 | ✅ Enhanced |
| `models.py` | Data layer | ~100 | ✅ Updated |
| `urls.py` | Routes | ~15 | ✅ Cleaned |

---

## 🚀 Payload Format

### React Format (RECOMMENDED)

```json
{
    "job_evn": {
        "environment": "value"
    },
    "job_steps": [
        {
            "identifier": "step1",
            "function": "record",
            "depends": [],
            "config": {
                "param1": "value1"
            }
        }
    ]
}
```

### Legacy Format (STILL WORKS)

```json
{
    "job_steps": [
        {"identifier": "step1", "function": "record"}
    ],
    "step1": {
        "param1": "value1"
    }
}
```

---

## 🔑 Key Features

### ✅ Atomic Transactions
```python
with transaction.atomic():
    # All database writes succeed together
    # Or all rollback together
```

### ✅ Deduplication
```python
fingerprint = compute_fingerprint(config)
# Identical configs share same hash
# No duplicate data in database
```

### ✅ Bulk Operations
```python
StepConfig.objects.bulk_create(configs)
JobStep.objects.bulk_create(steps)
# Much faster than loop.create()
```

### ✅ Type Hints
```python
def get_or_create_step_configs(
    data: dict, 
    job_steps_list: List[dict]
) -> Dict[str, str]:
    ...
```

---

## 📋 API Reference

### Create Job
```
POST /qmodel/jobs/
Content-Type: application/json
Authorization: Bearer <token>

{
    "job_evn": {...},
    "job_steps": [...]
}

Response (201):
{"id": "uuid...", "job_id": "uuid...", ...}
```

### Fetch Job (Worker)
```
GET /qmodel/getthenextjob/
Authorization: Bearer <token>

Response (200):
{
    "version": "0.4.1",
    "job_id": "uuid...",
    "job_evn": {...},
    "job_steps": [...],
    "step1": {...config...}
}
```

### Update Status (Worker)
```
POST /qmodel/getthenextjob/
Content-Type: application/json
Authorization: Bearer <token>

{
    "job_id": "uuid...",
    "step_id": "step1",
    "status": "running"
}

Response (200):
{"message": "Job step step1 status updated to running."}
```

---

## 🧪 Testing

### Run all tests
```bash
python manage.py test qmodel
```

### Test specific function
```bash
python manage.py test qmodel.tests.TestComputeFingerprint
```

### Test with coverage
```bash
coverage run --source='qmodel' manage.py test qmodel
coverage report
```

---

## 🐛 Debugging

### Check Django config
```bash
python manage.py check
```

### View database schema
```bash
python manage.py sqlmigrate qmodel 0002
```

### List all jobs
```bash
python manage.py shell
>>> from qmodel.models import Job
>>> Job.objects.all()
```

---

## 📚 Documentation Files

- **`QMODEL_REFACTOR_README.md`** - Complete architecture guide
- **`REFACTORING_SUMMARY.md`** - Summary of changes
- **`QUICK_REFERENCE.md`** - This file

---

## ✅ Checklist Before Deploying

- [ ] Run `python manage.py check`
- [ ] Run `python manage.py migrate`
- [ ] Run `python manage.py test qmodel`
- [ ] Update React frontend to POST to `/qmodel/jobs/`
- [ ] Test job submission from React
- [ ] Test worker job fetch
- [ ] Test worker status update
- [ ] Check database for created records
- [ ] Review logs for errors
- [ ] Deploy to production

---

## 🔗 Related Links

- **Main README:** `README.md`
- **Authentication:** `AUTHENTICATION_GUIDE.md`
- **Quick Start:** `QUICK_START.md`
- **Testing:** `TESTING_GUIDE.md`

---

## 💡 Pro Tips

1. **Use `/qmodel/job_list/`** to debug jobs in browser
2. **Check `/qmodel/jobs/`** in DRF to test API
3. **Enable query logging** to see N+1 problems
4. **Use type hints** when extending managers.py

---

**Last Updated:** November 20, 2025  
**Branch:** `qmodel-clean-architecture`  
**Status:** ✅ Ready for Production
