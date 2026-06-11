from django.contrib.auth.models import User
from django.db import models


class LabNote(models.Model):
    title = models.CharField(max_length=255, default="Untitled Note")
    content = models.TextField(blank=True, default="")  # stored as HTML
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lab_notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "lab_notebook_labnote"

    def __str__(self):
        return f"{self.title} ({self.created_by.username})"


class NoteAuditLog(models.Model):
    ACTION_CREATED = "created"
    ACTION_EDITED  = "edited"
    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_EDITED,  "Edited"),
    ]

    note      = models.ForeignKey(LabNote, on_delete=models.CASCADE, related_name="audit_logs")
    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="note_audit_logs")
    action    = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        db_table = "lab_notebook_auditlog"

    def __str__(self):
        return f"{self.note_id} — {self.action} by {self.user} at {self.timestamp:%Y-%m-%d %H:%M}"
