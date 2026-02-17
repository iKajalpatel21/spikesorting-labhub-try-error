from django.db import models
from job_queue.models import Job, JobStep, StepConfig


class JobCreationLog(models.Model):
    """
    Logs job creation requests for audit and debugging purposes.
    Tracks when jobs are created, with what parameters, and any errors that occur.
    """

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="creation_log",
        null=True,
        blank=True,
    )
    pipeline_id = models.IntegerField()  # Reference to the selected pipeline
    recording_config = models.JSONField()  # The recording config submitted
    job_env_preset = models.JSONField()  # The environment preset submitted
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Job Creation Log - Pipeline {self.pipeline_id} - {self.status}"

    class Meta:
        db_table = "jobs_jobcreationlog"
        ordering = ["-created_at"]
