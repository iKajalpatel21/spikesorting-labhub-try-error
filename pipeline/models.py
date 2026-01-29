from django.db import models
from qmodel.models import StepConfig


class Pipeline(models.Model):
    """
    Represents a pipeline configuration submitted by a researcher.
    """

    pipeline_id = models.AutoField(primary_key=True)
    description = models.TextField(help_text="Description of the pipeline")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pipeline"
        verbose_name_plural = "Pipelines"

    def __str__(self):
        return f"Pipeline {self.pipeline_id}: {self.description[:50]}"


class PipelineStep(models.Model):
    """
    Represents a single step in a pipeline, linking to StepConfig and optionally depending on a JobStep.
    """

    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="steps",
        help_text="The pipeline this step belongs to",
    )
    # Unique identifier for this pipeline step
    pipeline_step_id = models.AutoField(primary_key=True)
    # Function name (e.g., 'recording', 'preprocessing', 'sorting')
    function = models.CharField(
        max_length=64, default="", help_text="Step function name"
    )
    # Reference to the configuration block hash
    config_block_hash = models.ForeignKey(
        StepConfig,
        to_field="config_block_hash",
        on_delete=models.CASCADE,
        related_name="pipeline_steps",
        help_text="The configuration for this step",
    )
    # Step-specific configuration block
    config_block = models.ForeignKey(
        StepConfig,
        to_field="config_block",
        on_delete=models.CASCADE,
        related_name="pipeline_steps_config",
        help_text="Step-specific configuration",
        null=True,
        blank=True,
    )
    # Dependencies for this step (array of identifiers or JSON structure)
    depends_on = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="Step dependencies (identifiers of prerequisite steps)",
    )
