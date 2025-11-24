import json
import hashlib
from typing import Dict, List
from django.db import transaction
from .models import Job, JobStep, StepConfig


# ============================================================================
# STEP CONFIG OPERATIONS: Fingerprinting & Deduplication
# ============================================================================








# ============================================================================
# JOB CREATION OPERATIONS: Job + JobSteps in Atomic Transaction
# ============================================================================


def create_job_from_payload(payload_data: dict) -> Job:
    """
    Creates a complete Job with all its JobSteps and StepConfigs.
    Executes in a single atomic transaction for data consistency.

    WORKFLOW:
    1. Extract job_evn and job_steps from validated payload
    2. Process and deduplicate step configurations
    3. Create the main Job record
    4. Prepare JobStep objects for bulk creation
    5. Bulk create all JobSteps in one operation
    6. Return the created Job

    Key Features:
    - Atomic transaction ensures all-or-nothing persistence
    - Bulk operations optimize database writes
    - Deduplication via fingerprinting (StepConfig reuse)

    Args:
        payload_data (dict): Validated job payload with keys:
            - job_evn (dict): Job environment configuration
            - job_steps (List[dict]): Step definitions with identifier, function, depends

    Returns:
        Job: The newly created Job object with ID and related JobSteps

    Raises:
        ValueError: If payload is invalid or creation fails

    Example:
        >>> payload = {
        ...     'job_evn': {'env_var': 'value'},
        ...     'job_steps': [
        ...         {'identifier': 'step1', 'function': 'record', 'depends': []}
        ...     ],
        ...     'step1': {'config': 'data'}
        ... }
        >>> job = create_job_from_payload(payload)
        >>> print(job.job_id)  # UUID
    """
    
