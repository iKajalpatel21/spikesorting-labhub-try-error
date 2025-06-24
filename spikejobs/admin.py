from django.contrib import admin
from .models import Experiment

admin.site.register(Experiment)


class ExperimentAdmin(admin.ModelAdmin):
    list_display = ("job_type", "status", "submitted_at", "priority")
    search_fields = ("job_type", "status")
    list_filter = ("status", "submitted_at")
