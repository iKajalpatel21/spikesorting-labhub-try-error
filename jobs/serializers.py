from rest_framework import serializers
from qmodel.models import Job, JobStep, StepConfig
from pipeline.models import Pipeline
from .models import JobCreationLog


class RecordingConfigSerializer(serializers.Serializer):
    """Validates recording configuration from React wizard"""

    binfile = serializers.CharField(required=True, min_length=1)
    sampling_rate = serializers.IntegerField(required=True, min_value=1)
    num_channels = serializers.IntegerField(required=True, min_value=1)
    gain = serializers.FloatField(required=True)
    offset = serializers.FloatField(required=True)
    probe = serializers.CharField(required=False, allow_blank=True)


class CreateSortingJobSerializer(serializers.Serializer):
    """
    STEP 1: Validates React wizard payload

    Input from React:
    {
      "recording": {...},
      "pipeline_id": 1,
      "environment": "local"
    }
    """

    recording = RecordingConfigSerializer(required=True)
    pipeline_id = serializers.IntegerField(required=True, min_value=1)
    environment = serializers.ChoiceField(
        required=True, choices=["local", "gpu", "aws"]
    )

    def validate_pipeline_id(self, value):
        """Check if pipeline exists"""
        try:
            Pipeline.objects.get(pipeline_id=value)
        except Pipeline.DoesNotExist:
            raise serializers.ValidationError(f"Pipeline {value} does not exist")
        return value


class StepConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepConfig
        fields = ["config_block_hash", "config_block", "function"]
        read_only_fields = ["config_block_hash"]


class JobStepSerializer(serializers.ModelSerializer):
    config = StepConfigSerializer(source="config_block_hash", read_only=True)

    class Meta:
        model = JobStep
        fields = ["identifier", "function", "status", "depends_on", "config"]
        read_only_fields = ["identifier", "function", "status", "depends_on"]


class JobSerializer(serializers.ModelSerializer):
    steps = JobStepSerializer(source="jobstep_set", many=True, read_only=True)

    class Meta:
        model = Job
        fields = ["job_id", "status", "created_at", "job_env_config", "steps"]
        read_only_fields = ["job_id", "status", "created_at"]


class JobCreationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCreationLog
        fields = [
            "id",
            "job",
            "pipeline_id",
            "recording_config",
            "job_env_preset",
            "created_at",
            "status",
            "error_message",
        ]
        read_only_fields = ["id", "created_at"]
