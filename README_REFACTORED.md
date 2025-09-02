# Refactored QModel Worker - Clean Architecture

## 🏗️ Architecture Overview

This refactored version follows clean architecture principles with separation of concerns, dependency injection, and modular design.

## 📁 Project Structure

```
├── config/
│   ├── __init__.py
│   └── constants.py              # All URLs, tokens, and configuration constants
├── services/
│   ├── __init__.py
│   ├── api_service.py           # API communication service
│   ├── job_processor.py         # Job processing business logic
│   └── worker_service.py        # Main worker orchestration
├── qmodel/
│   ├── services/
│   │   ├── __init__.py
│   │   └── job_service.py       # Django job management service
│   ├── views_refactored.py      # Clean Django views
│   └── urls_refactored.py       # Organized URL configuration
├── qmodel_worker_refactored.py  # Main worker script
├── test_refactored_worker.py    # Test script
└── README_REFACTORED.md         # This file
```

## 🎯 Key Improvements

### ✅ **1. Configuration Management**
- **Before**: URLs and tokens scattered throughout code
- **After**: All configuration centralized in `config/constants.py`
- **Benefit**: Change one file to update all URLs/tokens

### ✅ **2. Function-Oriented Design**
- **Before**: Large monolithic functions
- **After**: Small, single-responsibility functions
- **Benefit**: Easier testing, debugging, and maintenance

### ✅ **3. Service-Based Architecture**
- **Before**: Direct API calls mixed with business logic
- **After**: Separate services for API, job processing, and orchestration
- **Benefit**: Clean separation of concerns

### ✅ **4. Environment Management**
- **Before**: Manual URL/token switching
- **After**: Simple environment flags (local, production, localhost_https)
- **Benefit**: Easy environment switching

### ✅ **5. Error Handling & Logging**
- **Before**: Inconsistent error handling
- **After**: Structured logging and error handling throughout
- **Benefit**: Better debugging and monitoring

## 🚀 Usage

### Quick Start

```bash
# Run in production environment (default)
python qmodel_worker_refactored.py

# Run in local development
python qmodel_worker_refactored.py --environment local

# Process single job and exit (testing)
python qmodel_worker_refactored.py --single

# Verbose logging
python qmodel_worker_refactored.py --verbose
```

### Test Components

```bash
# Test individual components
python test_refactored_worker.py
```

### Django Views

```python
# Use refactored views (update urls.py to import from views_refactored)
from qmodel import views_refactored as views
```

## 🔧 Configuration

### Environment Selection

```python
from config.constants import Environment

# Available environments
Environment.LOCAL           # http://localhost:8000
Environment.PRODUCTION      # https://128.164.33.148:8443  
Environment.LOCALHOST_HTTPS # https://localhost:8443
```

### Adding New URLs

```python
# config/constants.py
class APIEndpoints:
    NEW_ENVIRONMENT_URL = "https://new-server.com/api/"
    
class Environment:
    NEW_ENV = "new_env"
    
    @classmethod
    def get_api_url(cls, env=LOCAL):
        if env == cls.NEW_ENV:
            return APIEndpoints.NEW_ENVIRONMENT_URL
        # ... existing code
```

### Adding New Tokens

```python
# config/constants.py
class AuthTokens:
    NEW_TOKEN = "your-new-token-here"
    
class Environment:
    @classmethod
    def get_token(cls, env=LOCAL):
        if env == cls.NEW_ENV:
            return AuthTokens.NEW_TOKEN
        # ... existing code
```

## 🧪 Testing

### Unit Testing Individual Services

```python
from services.api_service import APIService
from config.constants import Environment

# Test API service
api = APIService(Environment.LOCAL)
job = api.get_next_job()
success = api.update_job_status("job-id", "completed")
```

### Integration Testing

```python
from services.worker_service import WorkerService

# Test full workflow
worker = WorkerService(Environment.LOCAL)
success = worker.process_single_job()
```

## 📊 Service Responsibilities

### APIService (`services/api_service.py`)
- HTTP communication with the API
- Authentication handling
- SSL/TLS configuration
- Request/response processing

### JobProcessor (`services/job_processor.py`)
- Job step execution logic
- Status management
- Error handling for job processing
- Job validation

### WorkerService (`services/worker_service.py`)
- Main worker loop orchestration
- Service coordination
- Lifecycle management
- Status reporting

### JobManagementService (`qmodel/services/job_service.py`)
- Django model operations
- Job creation from JSON
- Database transactions
- API response building

## 🔄 Migration from Old Worker

### Switching to Refactored Worker

1. **Stop old worker**:
   ```bash
   # Stop qmodel_worker.py
   pkill -f qmodel_worker.py
   ```

2. **Start refactored worker**:
   ```bash
   python qmodel_worker_refactored.py --environment production
   ```

3. **Update Django URLs** (optional):
   ```python
   # qmodel/urls.py - replace with:
   from .urls_refactored import urlpatterns
   ```

### Configuration Migration

Old configuration:
```python
# Scattered throughout code
API_URL = "https://128.164.33.148:8443/qmodel/getthenextjob/"
TOKEN = "df21421c859d47f3f712b1eb6d41813eab0afea4"
```

New configuration:
```python
# Centralized in config/constants.py
from config.constants import Environment
worker = WorkerService(Environment.PRODUCTION)
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Ensure you're in the project root directory
   cd /path/to/spikesorting-labhub-try-error
   python qmodel_worker_refactored.py
   ```

2. **API Connection Issues**:
   ```bash
   # Test API connectivity
   python test_refactored_worker.py
   ```

3. **Token Issues**:
   ```python
   # Update token in config/constants.py
   class AuthTokens:
       PRODUCTION_TOKEN = "your-working-token"
   ```

### Logging

The refactored worker provides detailed logging:

```bash
# Standard logging
python qmodel_worker_refactored.py

# Verbose logging
python qmodel_worker_refactored.py --verbose

# Log to file (modify worker script)
# Add file handler in setup_logging()
```

## 📈 Benefits Achieved

1. **✅ Single Source of Truth**: All URLs/tokens in one file
2. **✅ Modular Design**: Each service has a single responsibility  
3. **✅ Easy Testing**: Services can be tested independently
4. **✅ Environment Management**: Simple environment switching
5. **✅ Error Handling**: Consistent error handling throughout
6. **✅ Code Reusability**: Services can be reused across components
7. **✅ Maintainability**: Clean, readable, and well-documented code

## 🚀 Next Steps

1. **Deploy refactored worker** to production
2. **Update Django views** to use refactored versions
3. **Add unit tests** for each service
4. **Monitor performance** and optimize as needed
5. **Extend functionality** using the modular architecture

## 📝 Notes

- The original `qmodel_worker.py` is preserved for reference
- All functionality is maintained while improving structure
- The refactored code is backward compatible with existing API endpoints
- Environment switching is now much simpler and safer
