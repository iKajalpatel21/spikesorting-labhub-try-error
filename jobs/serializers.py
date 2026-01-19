from rest_framework import serializers
from qmodel.models import Job, JobStep, StepConfig
from .models import JobCreationLog


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
