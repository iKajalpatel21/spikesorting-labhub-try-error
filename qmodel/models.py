import uuid
import hashlib
import json
from django.db import models, transaction

# Choices for the 'status' field in Job and JobStep models
STATUS_CHOICES = [
    ("pending", "Pending"),
    ("fetched", "Fetched"),
    ("running", "Running"),
    ("finished", "Finished"),
    ("failed", "Failed"),
]


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


def get_or_create_step_configs(stepfunction: str, step_config: dict) -> str:
    """
    Gets or creates a StepConfig record in the database.
    Computes a fingerprint (SHA-256 hash) of the config block for deduplication.
    If the config already exists (same fingerprint), returns the existing fingerprint.
    Otherwise, creates a new StepConfig record and returns its fingerprint.

    Args:
        stepfunction: The name/type of the step function (e.g., 'recording', 'sorting')
        step_config: Dictionary containing the step configuration data

    Returns:
        str: SHA-256 fingerprint (hash) of the config block

    Raises:
        RuntimeError: If database operation fails
    """
    fingerprint = compute_fingerprint(step_config)
    if not StepConfig.objects.filter(config_block_hash=fingerprint).exists():
        try:
            stepconf = StepConfig(
                config_block_hash=fingerprint,
                config_block=step_config,
                function=stepfunction,  # Store function name
            )
            stepconf.save()
        except BaseException as e:
            raise RuntimeError(
                f"Cannot create a record in step database for function {stepfunction}: {e}"
            )
    return fingerprint


def create_a_job(job_evn: dict, job_steps: list) -> "Job":
    """
    Creates a Job with its associated JobSteps.
    Assumes all StepConfigs already exist in the database.

    Args:
        job_evn: Environment configuration dictionary for the job
        job_steps: List of step dictionaries, each containing:
                   - identifier: The config_block_hash (FK to StepConfig)
                   - function: The step function name
                   - depends: List of step identifiers this step depends on

    Returns:
        Job: The created Job object

    Raises:
        RuntimeError: If job_steps is empty or invalid
    """
    # Validation: Check job_steps is not empty
    if not len(job_steps):
        raise RuntimeError("job_steps are empty")

    # Validation: Check each step has required fields
    for setpid, step in enumerate(job_steps):
        if not isinstance(step, dict):
            raise RuntimeError(f"step #{setpid} is not a dictionary")

        for required_field in ["function", "identifier", "depends"]:
            if required_field not in step:
                raise RuntimeError(
                    f"step #{setpid} does not have '{required_field}' key"
                )

        # Validate that the config exists
        identifier = step["identifier"]
        if not StepConfig.objects.filter(config_block_hash=identifier).exists():
            raise RuntimeError(
                f"step #{setpid}: StepConfig with hash '{identifier}' does not exist. "
                f"Create the config first before creating the job."
            )

    # Create the Job and JobSteps atomically
    with transaction.atomic():
        # Create the main Job record
        job = Job.objects.create(job_env_config=job_evn, status="pending")

        # Prepare JobStep objects for bulk creation
        job_steps_objects = []
        for step in job_steps:
            job_steps_objects.append(
                JobStep(
                    identifier=step.get("identifier"),
                    job=job,
                    function=step.get("function"),
                    depends_on=step.get("depends", []),
                    config_block_hash_id=step.get("identifier"),  # FK to StepConfig
                    status="pending",
                )
            )

        # Bulk create all JobSteps
        JobStep.objects.bulk_create(job_steps_objects)

    return job


def get_next_job_id() -> "Job | None":
    """
    Fetches the next pending job and marks it as fetched (in progress).
    Uses row-level locking to prevent race conditions when multiple workers call this simultaneously.

    Returns:
        Job | None: The next pending job in FIFO order, or None if queue is empty
    """
    with transaction.atomic():
        # Select the oldest pending job with row lock to prevent race conditions
        job_to_process = (
            Job.objects.select_for_update()
            .filter(status="pending")
            .order_by("created_at")
            .first()
        )

        if job_to_process:
            job_to_process.status = "fetched"
            job_to_process.save()
        else:
            job_to_process = None
    return job_to_process


class Job(models.Model):
    """
    Represents a main job with its overall environment configuration.
    The 'job_id' from the uploaded JSON serves as the primary key, ensuring uniqueness.
    """

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Unique ID for the job (e.g., "c7df2f67-b3f6-460b")
    job_env_config = models.JSONField()  # Stores the 'job_evn' dictionary from the JSON
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending"
    )  # Current status of the job
    created_at = models.DateTimeField(
        auto_now_add=True
    )  # Automatically sets the timestamp when the job is created

    def __str__(self):
        """String representation for a Job object."""
        return str(self.job_id)  # Ensure this is a string


class StepConfig(models.Model):
    """
    Stores unique configuration blocks for individual job steps.
    The SHA-256 hash of the configuration JSON serves as its primary key,
    enabling efficient deduplication and lookup.
    """

    # This field holds the SHA-256 hash (fingerprint) of the config_block JSON
    config_block_hash = models.CharField(primary_key=True, max_length=64)
    config_block = models.JSONField()  # The actual JSON configuration data for a step
    function = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        """String representation for a StepConfig object."""
        return self.config_block_hash


class JobStep(models.Model):
    """
    Represents an individual step within a larger job.
    It links to its parent Job and to a specific, unique StepConfig.
    """

    # 'identifier' is the step's unique ID within its job (e.g., "7ea0910ccea1")
    identifier = models.CharField(max_length=64)

    # ForeignKey to the Job model, linking this step to its parent job.
    # 'to_field="job_id"' specifies that the foreign key links to the 'job_id' field of the Job model.
    # 'on_delete=models.CASCADE' means if the parent Job is deleted, this JobStep will also be deleted.
    job = models.ForeignKey(Job, to_field="job_id", on_delete=models.CASCADE)

    function = models.CharField(
        max_length=64
    )  # The name of the function for this step (e.g., "recording")

    # 'depends_on' stores a list of identifiers of other steps this step depends on.
    # 'null=True, blank=True' allows this field to be empty in the database and in forms.
    depends_on = models.JSONField(null=True, blank=True)

    # ForeignKey to the StepConfig model, linking this step to its specific configuration.
    # 'to_field="config_block_hash"' specifies that it links to the SHA-256 hash in StepConfig.
    config_block_hash = models.ForeignKey(
        "StepConfig", to_field="config_block_hash", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending"
    )  # Current status of this specific step

    class Meta:
        """
        Meta options for the JobStep model.
        'unique_together' ensures that the combination of 'job' and 'identifier' is unique.
        This is crucial because 'identifier' alone might not be unique across different jobs.
        For example, 'rec-001' can exist in multiple jobs, but 'rec-001' within 'job-alpha' is unique.
        """

        unique_together = ("job", "identifier")

    def __str__(self):
        """String representation for a JobStep object."""
        # Displays the job ID, step identifier, and function for easy identification
        return f"{self.job.job_id} - {self.identifier} ({self.function})"
