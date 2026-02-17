from rest_framework import serializers
from .models import Pipeline, PipelineStep
from job_queue.models import StepConfig, get_or_create_step_configs
import json


class PipelineStepSerializer(serializers.ModelSerializer):
    config_hash = serializers.CharField(
        source="config_block_hash.config_block_hash", read_only=True
    )
    function = serializers.CharField(
        source="config_block_hash.function", read_only=True
    )
    depends_on = serializers.JSONField(read_only=True)

    class Meta:
        model = PipelineStep
        fields = [
            "pipeline_step_id",
            "function",
            "config_hash",
            "depends_on",
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

    description = serializers.CharField(required=False, allow_blank=True)
    steps = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=False
    )
    job_steps = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=False
    )

    def create(self, validated_data):
        # Support both 'steps' and 'job_steps' field names
        steps_data = validated_data.get("steps") or validated_data.get("job_steps")
        description = validated_data.get("description", "Pipeline from JSON")

        # Get the raw request data to access config blocks that aren't in validated_data
        raw_data = self.initial_data if hasattr(self, "initial_data") else {}

        # Create pipeline
        pipeline = Pipeline.objects.create(description=description)

        # FIRST PASS: Create all StepConfigs and build mapping of placeholder to real config_block_hash
        placeholder_to_hash = (
            {}
        )  # Maps placeholder identifiers to actual config_block_hash values

        for idx, step_data in enumerate(steps_data):
            try:
                function = step_data.get("function")

                # Check if config is embedded or referenced by identifier
                config = step_data.get("config", {})
                if not config and "identifier" in step_data:
                    # For Pipeline_steps.json format: config is in a separate key
                    identifier = step_data.get("identifier")
                    # Try to get config from raw_data first (has all keys), then validated_data
                    config = raw_data.get(identifier) or validated_data.get(
                        identifier, {}
                    )

                if not function:
                    raise serializers.ValidationError(
                        f"Step {idx + 1} must have a 'function' field"
                    )

                # Call get_or_create_step_configs to create/get StepConfig
                config_block_hash_value = get_or_create_step_configs(function, config)

                # Store mapping: placeholder identifier -> actual config_block_hash
                placeholder_identifier = step_data.get("identifier")
                if placeholder_identifier:
                    placeholder_to_hash[placeholder_identifier] = (
                        config_block_hash_value
                    )

            except Exception as e:
                pipeline.delete()  # Rollback on error
                raise serializers.ValidationError(
                    f"Error creating step {idx + 1}: {str(e)}"
                )

        # SECOND PASS: Create PipelineSteps with resolved dependencies
        for idx, step_data in enumerate(steps_data):
            try:
                function = step_data.get("function")

                # Check if config is embedded or referenced by identifier
                config = step_data.get("config", {})
                if not config and "identifier" in step_data:
                    identifier = step_data.get("identifier")
                    config = raw_data.get(identifier) or validated_data.get(
                        identifier, {}
                    )

                # Get the config_block_hash that was created in first pass
                config_block_hash_value = get_or_create_step_configs(function, config)

                # RESOLVE DEPENDENCIES: Convert placeholder identifiers to actual config_block_hash values
                raw_depends = step_data.get("depends_on") or step_data.get(
                    "depends", []
                )
                resolved_depends = []

                for dep in raw_depends:
                    if dep in placeholder_to_hash:
                        # Convert placeholder to actual config_block_hash
                        resolved_depends.append(placeholder_to_hash[dep])
                    else:
                        # If it's already a real hash or unknown, keep as-is
                        resolved_depends.append(dep)

                # Create PipelineStep with resolved dependencies
                PipelineStep.objects.create(
                    pipeline=pipeline,
                    config_block_hash_id=config_block_hash_value,
                    depends_on=resolved_depends,  # NOW contains actual config_block_hash values
                )

            except Exception as e:
                pipeline.delete()  # Rollback on error
                raise serializers.ValidationError(
                    f"Error creating step {idx + 1}: {str(e)}"
                )

        return pipeline
