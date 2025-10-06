from rest_framework import serializers
from .models import Pipeline, PipelineStep
from qmodel.models import StepConfig, JobStep


class PipelineStepSerializer(serializers.ModelSerializer):
    step_config_hash = serializers.CharField(
        source="step_config.config_block_hash", read_only=True
    )
    depends_on_id = serializers.PrimaryKeyRelatedField(
        queryset=JobStep.objects.all(),
        source="depends_on",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = PipelineStep
        fields = [
            "id",
            "step_config",
            "step_config_hash",
            "depends_on",
            "depends_on_id",
            "order",
        ]


class PipelineSerializer(serializers.ModelSerializer):
    steps = PipelineStepSerializer(many=True, read_only=True)
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = Pipeline
        fields = ["pipeline_id", "description", "created_at", "steps", "step_count"]
        read_only_fields = ["pipeline_id", "created_at"]

    def get_step_count(self, obj):
        return obj.steps.count()


class PipelineCreateSerializer(serializers.Serializer):
    """Serializer for creating a pipeline with steps"""

    description = serializers.CharField(required=True)
    steps = serializers.ListField(
        child=serializers.DictField(), required=True, allow_empty=False
    )

    def create(self, validated_data):
        description = validated_data["description"]
        steps_data = validated_data["steps"]

        # Create pipeline
        pipeline = Pipeline.objects.create(description=description)

        # Create pipeline steps
        for idx, step_data in enumerate(steps_data):
            step_config_hash = step_data.get("step_config_hash")
            depends_on_id = step_data.get("depends_on_id")

            try:
                step_config = StepConfig.objects.get(config_block_hash=step_config_hash)
            except StepConfig.DoesNotExist:
                pipeline.delete()  # Rollback
                raise serializers.ValidationError(
                    f"StepConfig with hash {step_config_hash} not found"
                )

            depends_on = None
            if depends_on_id:
                try:
                    depends_on = JobStep.objects.get(id=depends_on_id)
                except JobStep.DoesNotExist:
                    pipeline.delete()  # Rollback
                    raise serializers.ValidationError(
                        f"JobStep with id {depends_on_id} not found"
                    )

            PipelineStep.objects.create(
                pipeline=pipeline,
                step_config=step_config,
                depends_on=depends_on,
                order=idx,
            )

        return pipeline
