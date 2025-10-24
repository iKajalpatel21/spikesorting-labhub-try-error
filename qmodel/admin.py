from django.contrib import admin
from .models import Job, JobStep, StepConfig

# Expose DRF Token in admin list so token keys are visible to admins
try:
    from rest_framework.authtoken.models import Token

    try:
        admin.site.unregister(Token)
    except Exception:
        # if it wasn't registered yet, ignore
        pass

    @admin.register(Token)
    class TokenAdmin(admin.ModelAdmin):
        list_display = ("key", "user")
        search_fields = ("key", "user__username", "user__email")
        readonly_fields = ("key",)
        ordering = ("-user",)

    # Some installations register a TokenProxy proxy model (name: tokenproxy)
    # which is what the default admin index links to. Try to register it too
    # so the admin link resolves and shows token keys.
    try:
        # TokenProxy may be defined in rest_framework.authtoken.admin
        from rest_framework.authtoken.admin import TokenProxy

        try:
            admin.site.unregister(TokenProxy)
        except Exception:
            pass

        @admin.register(TokenProxy)
        class TokenProxyAdmin(admin.ModelAdmin):
            list_display = ("key", "user")
            search_fields = ("key", "user__username", "user__email")
            readonly_fields = ("key",)
            ordering = ("-user",)

    except Exception:
        # If TokenProxy isn't available, that's fine — Token itself is registered
        pass
except Exception:
    # rest_framework.authtoken may not be installed in some environments
    pass


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin configuration for the Job model."""

    # 'job_id' is the primary key now, so use it instead of default 'id'
    # 'created_at' exists in the Job model
    list_display = ("job_id", "status", "created_at")
    # Allow searching by job_id
    search_fields = ("job_id",)
    # Allow filtering by status
    list_filter = ("status",)


@admin.register(StepConfig)
class StepConfigAdmin(admin.ModelAdmin):
    """Admin configuration for the StepConfig model."""

    # 'config_block_hash' is the primary key now, so use it
    # 'created_at' does NOT exist in StepConfig model, so remove it
    # 'fingerprint' was a conceptual name, the actual field is 'config_block_hash'
    list_display = ("config_block_hash", "config_block")
    # Allow searching by the hash
    search_fields = ("config_block_hash",)
    # Make config_block read-only in admin detail view if you don't want it editable
    # fields = ('config_block_hash', 'config_block')
    # readonly_fields = ('config_block_hash',) # Hash should not be editable


@admin.register(JobStep)
class JobStepAdmin(admin.ModelAdmin):
    """Admin configuration for the JobStep model."""

    # 'identifier' is the primary key for JobStep
    # 'job' is the ForeignKey to Job
    # 'config_block_hash' is the ForeignKey to StepConfig
    # 'created_at' does NOT exist in JobStep model, so remove it
    list_display = ("identifier", "job", "function", "config_block_hash", "status")
    # Allow searching by identifier and function
    search_fields = ("identifier", "function")
    # Allow filtering by job, function, and status
    list_filter = ("job", "function", "status")
    # Add raw_id_fields for ForeignKeys if you have many related objects
    # This can make the admin interface faster for selecting related objects
    raw_id_fields = ("job", "config_block_hash")
