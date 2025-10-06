from django.contrib import admin
from .models import Pipeline, PipelineStep


class PipelineStepInline(admin.TabularInline):
    model = PipelineStep
    extra = 1
    fields = ["step_config", "depends_on", "order"]
    autocomplete_fields = ["step_config", "depends_on"]


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
    list_display = ["id", "pipeline", "step_config_preview", "depends_on", "order"]
    list_filter = ["pipeline"]
    search_fields = ["pipeline__description", "step_config__config_block_hash"]
    autocomplete_fields = ["pipeline", "step_config", "depends_on"]
    ordering = ["pipeline", "order"]

    def step_config_preview(self, obj):
        return f"{obj.step_config.config_block_hash[:12]}..."

    step_config_preview.short_description = "Step Config"
