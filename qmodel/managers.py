import json
import hashlib
from typing import Dict, List
from django.db import transaction
from .models import Job, JobStep, StepConfig


# ============================================================================
# STEP CONFIG OPERATIONS: Fingerprinting & Deduplication
# ============================================================================


def compute_fingerprint(config_block: dict) -> str:
    """
    Generates a SHA-256 hash (fingerprint) for a given configuration block.
    Uses json.dumps with sorted keys to ensure consistent hash for identical content.

    Args:
        config_block (dict): Configuration dictionary to hash

    Returns:
        str: SHA-256 hex digest of the config block

    Example:
        >>> config = {'param': 'value', 'nested': {'key': 'data'}}
        >>> fp = compute_fingerprint(config)
        >>> print(len(fp))  # 64 (SHA-256 hex)
        64
    """
    json_str = json.dumps(config_block, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def get_or_create_step_configs(
    data: dict, job_steps_list: List[dict]
) -> Dict[str, str]:
    """
    Processes all step configurations from the payload.
    Returns a dict mapping step identifiers to their config block hashes.
    Handles deduplication via fingerprinting.

    Supports TWO payload formats:
    1. LEGACY (file upload): config_block at top level
       {'job_steps': [...], 'step1': {...config...}}
    2. REACT (new): config_block inside step
       {'job_steps': [{'identifier': 'step1', 'config': {...config...}}]}

    Key Features:
    - Detects format: checks step.get("config") first, falls back to data.get(identifier)
    - Computes fingerprint for each config block
    - Captures function name from job_steps for StepConfig
    - Bulk creates only new configs (skips existing ones)
    - Returns mapping of identifier -> hash for JobStep creation

    Args:
        data (dict): Full job payload containing step config blocks
        job_steps_list (List[dict]): List of step definitions with 'identifier' and 'function' keys

    Returns:
        Dict[str, str]: {identifier: config_block_hash, ...}

    Example (React format):
        >>> data = {
        ...     'job_evn': {...},
        ...     'job_steps': [{
        ...         'identifier': 'step1',
        ...         'function': 'record',
        ...         'config': {'param': 'value'}
        ...     }]
        ... }
        >>> result = get_or_create_step_configs(data, data['job_steps'])
        >>> # result = {'step1': 'abc123...def'}

    Example (Legacy format):
        >>> data = {
        ...     'job_steps': [{'identifier': 'step1', 'function': 'record'}],
        ...     'step1': {'param': 'value'}
        ... }
        >>> result = get_or_create_step_configs(data, data['job_steps'])
        >>> # result = {'step1': 'abc123...def'}
    """
    step_configs = {}
    step_config_objects = []

    # Process each step's configuration block
    for step in job_steps_list:
        identifier = step.get("identifier")
        function = step.get("function")  # Capture function name

        # Support both formats:
        # 1. React: config_block = step.get("config", {})
        # 2. Legacy: config_block = data.get(identifier, {})
        config_block = step.get("config") or data.get(identifier, {})

        fingerprint = compute_fingerprint(config_block)
        step_configs[identifier] = fingerprint

        # Check if this fingerprint already exists in DB
        if not StepConfig.objects.filter(config_block_hash=fingerprint).exists():
            step_config_objects.append(
                StepConfig(
                    config_block_hash=fingerprint,
                    config_block=config_block,
                    function=function,  # Store function name
                )
            )

    # Bulk create new configs (skips duplicates via ignore_conflicts)
    if step_config_objects:
        StepConfig.objects.bulk_create(step_config_objects, ignore_conflicts=True)

    return step_configs


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
    job_env_config = payload_data.get("job_evn", {})
    job_steps_list = payload_data.get("job_steps", [])

    with transaction.atomic():
        # Step 1: Process and deduplicate step configurations
        step_configs = get_or_create_step_configs(payload_data, job_steps_list)

        # Step 2: Create the main Job record
        job = Job.objects.create(job_env_config=job_env_config, status="pending")

        # Step 3: Prepare JobStep objects for bulk creation
        job_steps_objects = []
        for step in job_steps_list:
            identifier = step.get("identifier")
            function = step.get("function")
            depends_on = step.get("depends", [])
            config_hash = step_configs[identifier]

            job_steps_objects.append(
                JobStep(
                    identifier=identifier,
                    job=job,
                    function=function,
                    depends_on=depends_on,
                    config_block_hash_id=config_hash,
                    status="pending",
                )
            )

        # Step 4: Bulk create all JobSteps (more efficient than loop.create())
        JobStep.objects.bulk_create(job_steps_objects)

        return job
