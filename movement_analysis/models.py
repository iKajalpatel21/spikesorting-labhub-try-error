from django.contrib.auth.models import User
from django.db import models


class MovementSession(models.Model):
    """A single behavioural recording session containing movement tracking data."""

    name = models.CharField(max_length=255, default="Untitled Session")
    description = models.TextField(blank=True, default="")
    subject = models.CharField(max_length=255, blank=True, default="")
    recorded_at = models.DateTimeField(null=True, blank=True)
    sample_rate_hz = models.FloatField(null=True, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="movement_sessions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "movement_analysis_session"

    def __str__(self):
        return f"{self.name} ({self.created_by.username})"


class MovementTrack(models.Model):
    """Time-series position data for one tracked point (e.g. a body part / marker)."""

    session = models.ForeignKey(
        MovementSession, on_delete=models.CASCADE, related_name="tracks"
    )
    label = models.CharField(max_length=255, default="point")
    # JSON list of [t, x, y] (or [t, x, y, z]) samples
    samples = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]
        db_table = "movement_analysis_track"

    def __str__(self):
        return f"{self.label} — session {self.session_id}"
