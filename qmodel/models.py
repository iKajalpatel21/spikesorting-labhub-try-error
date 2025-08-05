# import uuid
# import hashlib
# from django.db import models

# # qmodel/models.py
# from django.db import models

# STATUS_CHOICES = [
#     ("pending", "Pending"),
#     ("fetched", "Fetched"),
#     ("running", "Running"),
#     ("finished", "Finished"),
#     ("failed", "Failed"),
# ]


# class Job(models.Model):
#     job_id = models.CharField(primary_key=True, max_length=64)  # From JSON
#     job_env_config = models.JSONField()  # Stores job_evn
#     status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.job_id


# class JobStep(models.Model):
#     identifier = models.CharField(primary_key=True, max_length=64)  # From JSON
#     job_id = models.ForeignKey(Job, to_field="job_id", on_delete=models.CASCADE)
#     function = models.CharField(max_length=64)
#     depends_on = models.JSONField(null=True, blank=True)
#     config_block_hash = models.ForeignKey(
#         "JobConfig", to_field="identifier", on_delete=models.CASCADE
#     )
#     status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")

#     def __str__(self):
#         return f"{self.identifier} ({self.function})"


# class JobConfig(models.Model):
#     identifier = models.CharField(primary_key=True, max_length=64)  # SHA-256 hash
#     config_block = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)


#     def __str__(self):
#         return self.identifier

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


class Job(models.Model):
    """
    Represents a main job with its overall environment configuration.
    The 'job_id' from the uploaded JSON serves as the primary key, ensuring uniqueness.
    """

    job_id = models.CharField(
        primary_key=True, max_length=64
    )  # Unique ID for the job (e.g., "c7df2f67-b3f6-460b")
    job_env_config = models.JSONField()  # Stores the 'job_evn' dictionary from the JSON
    status = models.CharField(
        max_length=32, choices=STATUS_CHOICES, default="pending"
    )  # Current status of the job
    created_at = models.DateTimeField(
        auto_now_add=True
    )  # Automatically sets the timestamp when the job is created

    def __str__(self):
        """String representation for a Job object."""
        return self.job_id


class StepConfig(models.Model):
    """
    Stores unique configuration blocks for individual job steps.
    The SHA-256 hash of the configuration JSON serves as its primary key,
    enabling efficient deduplication and lookup.
    """

    # This field holds the SHA-256 hash (fingerprint) of the config_block JSON
    config_block_hash = models.CharField(primary_key=True, max_length=64)
    config_block = models.JSONField()  # The actual JSON configuration data for a step

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
