import uuid
import hashlib
from django.db import models

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
    
    
def get_or_create_step_configs(
    stepfunction: str, step_config: dict
) -> str:
    '''
    this function put a step config in the database. 
    it computes fingerprint, checks if fingerprint is there return just finger print
    if not it creates a recording in StepConfig tablet and returns new finger print
    '''
    fingerprint = compute_fingerprint(step_config)
    if not StepConfig.objects.filter(config_block_hash=fingerprint).exists():
        try:
            stepconf =  StepConfig(
                config_block_hash=fingerprint,
                config_block=config_block,
                function=function,  # Store function name
            )
            stepconf.save()
        except BaseException as e:
            raise RuntimeError(f'Cannot create a record in step database for function {stepfunction}: {e}'
    return fingerprint

def create_a_job(job_evn:dict, job_steps:list)->str:
    if len(job_steps) :
        raise RuntimeError(f'job_steps are empty')
    for setpid, step in enumerate(job_steps):
        if not type(step) is dict:
            raise RuntimeError(f'step #{setpid} is not a dictionary')
        for n in 'function identifier depends'.split():
            if not n in step:
                raise RuntimeError(f'step #{setpid} does not have {n} key')
        function   = step['function']
        identifier = step['identifier']
        if not StepConfig.objects.filter(config_block_hash=identifier).exists():
            raise RuntimeError(f'Step config for function {function} with identifier {identifier} does not exist in step config table')
    
    with transaction.atomic():
        # Step 2: Create the main Job record
        job = Job.objects.create(job_env_config=job_evn, status="pending")

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

def get_next_job_id()->(Job, None):
    with transaction.atomic():
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
