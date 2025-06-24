from django.db import models

# class Experiment(models.Model):
#     name = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)


class Experiment(models.Model):
    job_type = models.CharField(max_length=50, default="sorting")
    parameters = models.JSONField()
    status = models.CharField(max_length=20)
    submitted_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=1)
    result_path = models.CharField(max_length=255, blank=True)
    log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.job_type} - {self.status} ({self.submitted_at})"
