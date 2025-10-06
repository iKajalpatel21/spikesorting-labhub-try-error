from django.db import models
from qmodel.models import StepConfig, JobStep


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
    step_config = models.ForeignKey(
        StepConfig,
        to_field="config_block_hash",
        on_delete=models.CASCADE,
        related_name="pipeline_steps",
        help_text="The configuration for this step",
    )
    depends_on = models.ForeignKey(
        JobStep,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dependent_pipeline_steps",
        help_text="Optional: The job step this pipeline step depends on",
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Execution order within the pipeline"
    )

    class Meta:
        ordering = ["pipeline", "order"]
        unique_together = [["pipeline", "step_config"]]
        verbose_name = "Pipeline Step"
        verbose_name_plural = "Pipeline Steps"

    def __str__(self):
        return f"Pipeline {self.pipeline.pipeline_id} → StepConfig {self.step_config.config_block_hash[:8]}"
