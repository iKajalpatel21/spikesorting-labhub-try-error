from rest_framework import serializers
from job_queue.models import Job, JobStep, StepConfig
from pipeline_factory.models import Pipeline
from .models import JobCreationLog


class RecordingConfigSerializer(serializers.Serializer):
    """Validates recording configuration from React wizard"""

    binfile = serializers.CharField(required=True, min_length=1)
    sampling_rate = serializers.IntegerField(required=True, min_value=1)
    num_channels = serializers.IntegerField(required=True, min_value=1)
    gain = serializers.FloatField(required=True)
    offset = serializers.FloatField(required=True)
    probe = serializers.CharField(required=False, allow_blank=True)
    bad_channels = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )


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


class JobStepSerializer(serializers.ModelSerializer):
    """Serialize individual job steps"""

    config_block = serializers.SerializerMethodField()

    class Meta:
        model = JobStep
        fields = ["identifier", "function", "status", "depends_on", "config_block"]
        read_only_fields = ["identifier", "function", "status", "depends_on"]

    def get_config_block(self, obj):
        """Get the config block from the StepConfig"""
        if obj.config_block_hash:
            return obj.config_block_hash.config_block
        return {}


class JobListSerializer(serializers.ModelSerializer):
    """Serialize jobs for list/detail view"""

    job_steps = JobStepSerializer(source="jobstep_set", many=True, read_only=True)
    step_count = serializers.SerializerMethodField()
    completed_steps = serializers.SerializerMethodField()
    job_env = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "job_id",
            "status",
            "created_at",
            "job_env",
            "step_count",
            "completed_steps",
            "job_steps",
        ]
        read_only_fields = ["job_id", "status", "created_at"]

    def get_step_count(self, obj):
        return obj.jobstep_set.count()

    def get_completed_steps(self, obj):
        return obj.jobstep_set.filter(status="finished").count()

    def get_job_env(self, obj):
        """Extract key info from job environment config"""
        env = obj.job_env_config or {}
        return {
            "environment": env.get("job_kwargs", {}).get("environment", "unknown"),
            "log_level": env.get("log_level", "INFO"),
            "base_directory": env.get("base_directory", "/tmp"),
        }


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
