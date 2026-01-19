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
    step_config = models.ForeignKey(
        StepConfig,
        to_field="config_block_hash",
        on_delete=models.CASCADE,
        related_name="pipeline_steps",
        help_text="The configuration for this step",
    )
    # Previously this was a ForeignKey to JobStep. To support pipeline-local
    # dependency information coming from uploaded JSON we store an array of
    # identifiers (or any JSON structure) directly on the model.
    depends_on = models.JSONField(default=list, null=True, blank=True)
    # Order field for explicit step ordering within pipeline
    order = models.IntegerField(default=0, help_text="Execution order within pipeline")
    # Function name (e.g., 'recording', 'preprocessing', 'sorting')
    function = models.CharField(max_length=64, default='', help_text="Step function name")
    # Configuration block for this step
    config = models.JSONField(null=True, blank=True, help_text="Step-specific configuration")


class Recording(models.Model):
    bin_file = models.FileField(upload_to="recordings/")
    probe_file = models.FileField(upload_to="probes/")
    sampling_rate = models.FloatField()
    num_channels = models.IntegerField()
    gain_to_uV = models.FloatField()
    offset_to_uV = models.FloatField()
    remove_channels = models.JSONField(default=list)
    bad_channels = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    step_config = models.ForeignKey(
        StepConfig,
        on_delete=models.CASCADE,
        related_name="recordings",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recording"
        verbose_name_plural = "Recordings"

    def __str__(self):
        return (
            f"Recording {self.id} (StepConfig {self.step_config.config_block_hash[:8]})"
        )
