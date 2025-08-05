from django.contrib import admin
from .models import Job, JobStep, JobConfig


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("id",)


@admin.register(JobStep)
class JobStepAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "function", "status", "created_at")
    list_filter = ("status", "function")
    search_fields = ("id", "job__id")


@admin.register(JobConfig)
class JobConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "fingerprint", "created_at")
    search_fields = ("fingerprint",)
