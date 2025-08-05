import uuid
import hashlib
from django.db import models

STATUS_CHOICES = [
    ("pending", "Pending"),
    ("fetched", "Fetched"),
    ("running", "Running"),
    ("finished", "Finished"),
    ("failed", "Failed"),
]


class JobConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fingerprint = models.CharField(max_length=64, unique=True)  # SHA256 hex length
    raw_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def compute_fingerprint(json_obj):
        raw_str = str(json_obj).encode("utf-8")
        return hashlib.sha256(raw_str).hexdigest()


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(JobConfig, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


class JobStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="steps")
    function = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100)  # ← Add this line
    depends_on = models.JSONField(default=list)  # list of JobStep IDs
    config = models.JSONField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)


# # qmodel/models.py

# from django.db import models


# class JobConfig(models.Model):
#     fingerprint = models.TextField()
#     raw_json = models.JSONField()


# class Job(models.Model):
#     job_id = models.CharField(
#         primary_key=True, max_length=64
#     )  # used from JSON (e.g., "c7df2f67-b3f6-460b")
#     config = models.ForeignKey(JobConfig, on_delete=models.CASCADE)
#     status = models.CharField(max_length=20, default="pending")
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.job_id


# class JobStep(models.Model):
#     id = models.CharField(
#         primary_key=True, max_length=64
#     )  # step id like "754fed717d11"
#     job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="steps")
#     function = models.CharField(max_length=100)
#     depends_on = models.JSONField()  # list of ids
#     config = models.JSONField()  # raw config block
#     status = models.CharField(max_length=20, default="pending")

#     def __str__(self):
#         return f"{self.id} ({self.function})"
