from django.db import models


class Experiment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("fetched", "Fetched"),  # ✅ Add this because your worker sets it
        ("running", "Running"),
        ("finished", "Finished"),
        ("failed", "Failed"),
    ]

    job_type = models.CharField(max_length=50, default="sorting")
    parameters = models.JSONField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )  # ✅
    submitted_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=1)
    result_path = models.CharField(max_length=255, blank=True)
    log_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.job_type} - {self.status} ({self.submitted_at})"
