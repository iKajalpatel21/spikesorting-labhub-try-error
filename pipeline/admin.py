from django.contrib import admin
from .models import Pipeline, PipelineStep
from .models import Recording


class PipelineStepInline(admin.TabularInline):
    model = PipelineStep
    extra = 1
    fields = ["step_config", "depends_on"]
    # 'depends_on' is a JSONField (pipeline-local identifiers) so it is not
    # suitable for admin autocomplete. Keep step_config as FK autocomplete
    # if StepConfig is registered to support it.
    autocomplete_fields = ["step_config"]


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ["pipeline_id", "description_preview", "created_at", "step_count"]
    list_filter = ["created_at"]
    search_fields = ["description"]
    readonly_fields = ["created_at"]
    inlines = [PipelineStepInline]

    def description_preview(self, obj):
        return (
            obj.description[:100] + "..."
            if len(obj.description) > 100
            else obj.description
        )

    description_preview.short_description = "Description"

    def step_count(self, obj):
        return obj.steps.count()

    step_count.short_description = "Steps"


@admin.register(PipelineStep)
class PipelineStepAdmin(admin.ModelAdmin):
    list_display = ["id", "pipeline", "step_config_preview", "depends_on"]
    list_filter = ["pipeline"]
    search_fields = ["pipeline__description", "step_config__config_block_hash"]
    # depends_on is a JSONField and not a FK/M2M, so remove it from autocomplete
    autocomplete_fields = ["pipeline", "step_config"]
    # Execution order is inferred from the step insertion/array order; remove
    # explicit ordering by the removed 'order' field.
    ordering = ["pipeline"]

    def step_config_preview(self, obj):
        return f"{obj.step_config.config_block_hash[:12]}..."

    step_config_preview.short_description = "Step Config"


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "bin_file",
        "probe_file",
        "sampling_rate",
        "num_channels",
        "created_at",
        "step_config",
    ]
    readonly_fields = ["created_at"]
    search_fields = ["step_config__config_block_hash"]
    list_filter = ["created_at"]
