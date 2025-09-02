"""
Configuration constants for the spikesorting-labhub application.
This file contains all URLs, tokens, and other configuration values used throughout the application.
"""

# =============================================================================
# API ENDPOINTS
# =============================================================================
class APIEndpoints:
    """API endpoint configurations"""
    
    # Local development URLs
    LOCAL_BASE_URL = "http://localhost:8000"
    LOCAL_API_URL = f"{LOCAL_BASE_URL}/qmodel/getthenextjob/"
    
    # Production URLs  
    PRODUCTION_BASE_URL = "https://128.164.33.148:8443"
    PRODUCTION_API_URL = f"{PRODUCTION_BASE_URL}/qmodel/getthenextjob/"
    
    # Alternative localhost HTTPS
    LOCALHOST_HTTPS_URL = "https://localhost:8443/qmodel/getthenextjob/"

# =============================================================================
# AUTHENTICATION TOKENS
# =============================================================================
class AuthTokens:
    """Authentication token configurations"""
    
    # Working tokens
    LOCAL_TOKEN = "df21421c859d47f3f712b1eb6d41813eab0afea4"
    PRODUCTION_TOKEN = "df21421c859d47f3f712b1eb6d41813eab0afea4"
    
    # Legacy/Invalid tokens (kept for reference)
    OLD_PRODUCTION_TOKEN = "d26381352d1b6532591b7aceb07bf1630e72183a"
    LEGACY_TOKEN = "e1997396f5c992a1cc89ea5c8a518ab22bbab65f"

# =============================================================================
# WORKER CONFIGURATION
# =============================================================================
class WorkerConfig:
    """Worker process configuration"""
    
    POLLING_INTERVAL_SECONDS = 5
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 1
    
    # SSL Configuration
    SSL_VERIFY = False
    SSL_CERT_PATH = "cert.pem"
    
    # Logging configuration
    LOG_FORMAT = "%(asctime)s - %(lineno)-6d - %(levelname)s - %(message)s"
    LOG_LEVEL = "INFO"

# =============================================================================
# JOB SPECIFICATION
# =============================================================================
class JobSpecification:
    """Job specification constants"""
    
    VERSION = "0.4.1"
    SI_VERSION = "0.101.0"
    
    # Job statuses
    STATUS_PENDING = "pending"
    STATUS_FETCHED = "fetched"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FINISHED = "finished"
    STATUS_FAILED = "failed"

# =============================================================================
# ENVIRONMENT SELECTION
# =============================================================================
class Environment:
    """Environment configuration selector"""
    
    LOCAL = "local"
    PRODUCTION = "production"
    LOCALHOST_HTTPS = "localhost_https"
    
    @classmethod
    def get_api_url(cls, env=LOCAL):
        """Get API URL for specified environment"""
        if env == cls.LOCAL:
            return APIEndpoints.LOCAL_API_URL
        elif env == cls.PRODUCTION:
            return APIEndpoints.PRODUCTION_API_URL
        elif env == cls.LOCALHOST_HTTPS:
            return APIEndpoints.LOCALHOST_HTTPS_URL
        else:
            raise ValueError(f"Unknown environment: {env}")
    
    @classmethod
    def get_token(cls, env=LOCAL):
        """Get authentication token for specified environment"""
        if env == cls.LOCAL:
            return AuthTokens.LOCAL_TOKEN
        elif env == cls.PRODUCTION:
            return AuthTokens.PRODUCTION_TOKEN
        else:
            return AuthTokens.LOCAL_TOKEN

# =============================================================================
# TEMPLATE PATHS
# =============================================================================
class TemplatePaths:
    """Template file paths"""
    
    JOB_LIST = "qmodel/job_list.html"
    SUBMIT_JSON = "qmodel/qmodel_submit_json.html"

# =============================================================================
# ERROR MESSAGES
# =============================================================================
class ErrorMessages:
    """Standard error messages"""
    
    INVALID_JSON = "❌ Error: Invalid JSON file format."
    MISSING_JOB_STEPS = "JSON file is missing 'job_steps'."
    JOB_ID_STATUS_REQUIRED = "Job ID and status are required."
    INVALID_JSON_FORMAT = "Invalid JSON format."
    
    # Success messages
    JOB_SUBMITTED_SUCCESS = "✅ Job submitted successfully! ID: {job_id}"
    JOB_STATUS_UPDATED = "Job {job_id} status updated to {status}."
    JOB_STEP_STATUS_UPDATED = "Job step {step_id} status updated to {status}."
