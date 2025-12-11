# QModel Clean Architecture - Project Summary

**Last Updated:** December 10, 2025  
**Branch:** `qmodel-clean-architecture`  
**Status:** ✅ Production Ready

---

## 📋 Project Overview

This is a Django REST API backend for managing spike sorting job queues with a clean architecture following SOLID principles. The system handles job submission from React frontends, manages worker queues, and processes jobs with multiple dependent steps.

---

## 📁 Workspace Organization

### Core Application Files

```
qmodel/                          # Main Django app
├── models.py                    # Django models + 4 core pure functions
├── views.py                     # 2 REST API endpoints
├── serializers.py               # Input validation
├── urls.py                      # URL routing
├── tests.py                     # 38+ comprehensive tests
├── migrations/                  # Database migrations
└── templates/                   # Admin templates (optional)
```

### Documentation

```
DEVELOPMENT_GUIDE.md             # ⭐ MAIN REFERENCE (consolidated guide)
README.md                        # Project overview
README_QMODEL.md                 # Legacy QModel documentation
```

### Testing & Example Files

```
test_job.json                    # Example job submission format
requirements.txt                 # Python dependencies
manage.py                        # Django management
```

### Configuration & Deployment

```
labhub/                          # Django project directory
├── settings.py
├── urls.py
├── wsgi.py
└── asgi.py

deploy.sh                        # Production deployment script
github_deploy.sh                 # GitHub Actions deployment
simple_deploy.sh                 # Simple deployment script
qmodel_worker.py                 # Worker process script
```

### Frontend (React)

```
my-app/                          # React app
├── src/
│   ├── App.js
│   ├── components/
│   │   └── ProtectedRoute.js
│   ├── pages/
│   │   └── LoginPage.js
│   ├── context/
│   │   └── AuthContext.js
│   └── services/
│       └── authService.js
├── public/
└── package.json
```

### Removed Files (Consolidated)

The following files have been removed as their content was consolidated into `DEVELOPMENT_GUIDE.md`:

- ❌ `QUICK_REFERENCE.md` → consolidated
- ❌ `QMODEL_REFACTOR_README.md` → consolidated  
- ❌ `REFACTORING_SUMMARY.md` → consolidated

---

## 🎯 Key Components

### 1. Pure Functions (models.py)

Four core functions handling business logic:

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `compute_fingerprint()` | SHA-256 hashing for deduplication | dict config | str hash (64 chars) |
| `get_or_create_step_configs()` | Create/reuse configs with deduplication | function name, config dict | str fingerprint |
| `create_a_job()` | Orchestrate atomic job creation | job_env dict, job_steps list | Job object |
| `get_next_job_id()` | FIFO worker queue with locking | None | Job \| None |

### 2. Models (Django ORM)

Three interconnected models:

- **Job:** Main job record with environment config
- **StepConfig:** Reusable configuration blocks (deduplicated by SHA-256 hash)
- **JobStep:** Individual steps linking Job → StepConfig

### 3. Views (REST API)

Two focused endpoints:

- **JobViewSet:** REST CRUD operations for jobs (`/qmodel/jobs/`)
- **get_next_job():** Worker job fetch/status update (`/qmodel/getthenextjob/`)

### 4. Serializers (Validation)

- **JobSerializer:** Job serialization
- **JobCreationPayloadSerializer:** Input validation for job creation

---

## 📊 Test Coverage

### 38+ Comprehensive Tests

```
TestComputeFingerprint (10 tests)
├─ Hash consistency
├─ Key ordering (doesn't affect hash)
├─ Edge cases (empty dict, complex nested)
└─ Type handling (int vs float, string vs number)

TestGetOrCreateStepConfigs (4 tests)
├─ Config creation
├─ Config reuse (deduplication)
├─ Function name storage
└─ Different configs → different fingerprints

TestCreateAJob (7 tests)
├─ Single/multiple steps
├─ Validation (empty, non-dict, missing fields)
├─ Config existence check
└─ Dependency preservation

TestGetNextJobId (5 tests)
├─ FIFO ordering
├─ Row-level locking
├─ Status transitions (pending → fetched)
└─ Non-pending job skipping

TestModelRules (12 tests)
├─ Model constraints
├─ JSON field storage
├─ Relationships
├─ Default values
└─ Status transitions
```

**Run tests:**
```bash
python manage.py test qmodel -v 2
```

---

## 🚀 Quick Reference

### Setup
```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test qmodel
```

### API Endpoints

**React: Create Job**
```
POST /qmodel/jobs/
{
  "job_evn": {...},
  "job_steps": [
    {"identifier": "step1", "function": "record", "depends": [], "config": {...}}
  ]
}
```

**Worker: Fetch Job**
```
GET /qmodel/getthenextjob/
Response: {"job_id": "uuid...", "job_steps": [...], "step1": {...config...}}
```

**Worker: Update Status**
```
POST /qmodel/getthenextjob/
{"job_id": "uuid...", "step_id": "step1", "status": "running"}
```

---

## 📚 Documentation Strategy

### Single Source of Truth

**Primary Reference:** `DEVELOPMENT_GUIDE.md`
- Complete architecture overview
- API reference with examples
- Code structure & pure functions
- Data flow diagrams
- Testing guide
- Deployment instructions
- Troubleshooting

### Supporting Files

- `README.md` - Project overview
- `README_QMODEL.md` - Legacy documentation (keep for historical reference)
- `test_job.json` - Example job format
- Code comments - Inline documentation with docstrings

---

## ✅ Quality Metrics

| Aspect | Status |
|--------|--------|
| **Type Coverage** | ✅ 100% (full type hints) |
| **Test Coverage** | ✅ 38+ tests, all passing |
| **Documentation** | ✅ Comprehensive (DEVELOPMENT_GUIDE.md) |
| **Code Quality** | ✅ SOLID principles applied |
| **Performance** | ✅ Bulk operations, deduplication, locking |
| **Atomicity** | ✅ Transaction-based all-or-nothing |

---

## 🔄 Workflow Summary

1. **React Frontend** sends job JSON to `/qmodel/jobs/`
2. **JobViewSet.create()** validates and processes
3. **create_a_job()** orchestrates atomic creation with:
   - Config deduplication via `compute_fingerprint()`
   - Job creation
   - Bulk JobStep creation
4. **Worker** calls `GET /qmodel/getthenextjob/` to fetch next job
5. **get_next_job_id()** returns oldest pending job with row-level lock
6. **Worker** processes and calls `POST /qmodel/getthenextjob/` to update status

---

## 📖 Where to Find What

| Need | Location |
|------|----------|
| API usage examples | `DEVELOPMENT_GUIDE.md` → API Reference section |
| Test examples | `qmodel/tests.py` → 38+ tests |
| Database schema | `qmodel/models.py` → Model classes |
| Business logic | `qmodel/models.py` → 4 core functions |
| Deployment | `DEVELOPMENT_GUIDE.md` → Deployment section |
| Troubleshooting | `DEVELOPMENT_GUIDE.md` → Troubleshooting section |
| Example payloads | `test_job.json` |

---

## 🎓 Key Concepts

### Deduplication (SHA-256 Fingerprinting)
Identical configurations share one StepConfig record to save database space:
```python
config1 = {"duration": 60, "sample_rate": 30000}
config2 = {"sample_rate": 30000, "duration": 60}  # Different order, same config

# Both produce same hash
hash1 = compute_fingerprint(config1)
hash2 = compute_fingerprint(config2)
# hash1 == hash2 ✓
```

### FIFO Worker Queue with Locking
Prevents race conditions when multiple workers fetch jobs:
```python
job = Job.objects.select_for_update().filter(status='pending').first()
# Row-level lock ensures only one worker gets this job
```

### Atomic Transactions
All database writes succeed together or rollback:
```python
with transaction.atomic():
    job = Job.objects.create(...)
    JobStep.objects.bulk_create(steps)
    # If either fails, entire transaction rolls back
```

---

## 📊 Database Schema

```
┌─────────────────────────────────────────────────┐
│ Job                                             │
├─────────────────────────────────────────────────┤
│ job_id (UUID, PK)                               │
│ status (CharField)                              │
│ job_env_config (JSONField)                      │
│ created_at (DateTimeField)                      │
└──────────────┬──────────────────────────────────┘
               │ (1 to Many)
               ↓
┌─────────────────────────────────────────────────┐
│ JobStep                                         │
├─────────────────────────────────────────────────┤
│ id (AutoField, PK)                              │
│ job (ForeignKey → Job)                          │
│ identifier (CharField)                          │
│ function (CharField)                            │
│ config_block_hash (ForeignKey → StepConfig)     │
│ status (CharField)                              │
│ depends_on (JSONField, list)                    │
└──────────────┬──────────────────────────────────┘
               │ (Many to 1)
               ↓
┌─────────────────────────────────────────────────┐
│ StepConfig                                      │
├─────────────────────────────────────────────────┤
│ config_block_hash (CharField, PK)               │
│ config_block (JSONField)                        │
│ function (CharField)                            │
└─────────────────────────────────────────────────┘
```

---

## 🔐 Security Notes

- Token-based authentication for API endpoints
- CSRF protection enabled
- Input validation via serializers
- Row-level database locking prevents race conditions
- Type hints catch many bugs at development time

---

## 🚀 Production Checklist

- [ ] Run `python manage.py check`
- [ ] Run migrations: `python manage.py migrate`
- [ ] Run tests: `python manage.py test qmodel`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Update React frontend to POST to `/qmodel/jobs/`
- [ ] Test job submission from React
- [ ] Test worker job fetch
- [ ] Verify database backups
- [ ] Monitor error logs
- [ ] Deploy using `deploy.sh` or GitHub Actions

---

## 📞 Support

- **Main Guide:** `DEVELOPMENT_GUIDE.md`
- **Code Comments:** Read docstrings in Python files
- **Tests:** Run tests to validate changes
- **Examples:** Check `test_job.json` for payload format

---

**Status:** ✅ Production Ready | **Documentation:** ✅ Complete | **Tests:** ✅ 38+ Passing
