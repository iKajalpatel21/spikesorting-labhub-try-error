from rest_framework import serializers
from .models import Pipeline, PipelineStep, Recording
from qmodel.models import StepConfig


class PipelineStepSerializer(serializers.ModelSerializer):
    step_config_hash = serializers.CharField(
        source="step_config.config_block_hash", read_only=True
    )
    # depends_on now stores pipeline-local identifiers (JSON) so expose as-is
    depends_on = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = PipelineStep
        fields = [
            "id",
            "step_config",
            "step_config_hash",
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
            # Support either a provided config_block (full JSON) or an existing hash
            step_config = None
            if "config_block" in step_data:
                config_block = step_data.get("config_block")
                # Extract 'depends' from config_block before hashing (so it's not part of the hash)
                depends_on = config_block.pop("depends", [])

                # Compute deterministic hash for the provided config block
                try:
                    import json as _json, hashlib as _hashlib

                    json_text = _json.dumps(
                        config_block, sort_keys=True, separators=(",", ":")
                    )
                    step_hash = _hashlib.sha256(json_text.encode("utf-8")).hexdigest()
                except Exception:
                    pipeline.delete()
                    raise serializers.ValidationError("Invalid config_block provided")

                step_config, created = StepConfig.objects.get_or_create(
                    config_block_hash=step_hash, defaults={"config_block": config_block}
                )
            else:
                # Fall back to existing step_config_hash
                step_config_hash = step_data.get("step_config_hash")
                if not step_config_hash:
                    pipeline.delete()
                    raise serializers.ValidationError(
                        "Each step must include either 'config_block' or 'step_config_hash'"
                    )
                try:
                    step_config = StepConfig.objects.get(
                        config_block_hash=step_config_hash
                    )
                except StepConfig.DoesNotExist:
                    pipeline.delete()  # Rollback
                    raise serializers.ValidationError(
                        f"StepConfig with hash {step_config_hash} not found"
                    )
                # Extract depends_on from step_data if using existing hash
                depends_on = step_data.get("depends_on") or []

            # For Option 1 we record pipeline-local dependency identifiers
            # (depends_on already extracted above)

            PipelineStep.objects.create(
                pipeline=pipeline,
                step_config=step_config,
                depends_on=depends_on,
            )

        return pipeline


class RecordingSerializer(serializers.ModelSerializer):
    # step_config is computed server-side and therefore read-only for clients
    step_config = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recording
        fields = [
            "id",
            "bin_file",
            "probe_file",
            "sampling_rate",
            "num_channels",
            "gain_to_uV",
            "offset_to_uV",
            "remove_channels",
            "bad_channels",
            "created_at",
            "step_config",
        ]
        read_only_fields = ["id", "created_at"]
        # step_config is read-only; server computes and attaches it

    def create(self, validated_data):
        import json
        import hashlib

        # Pop the optional step_config if provided so super().create() won't try to use it
        provided_step_config = validated_data.pop("step_config", None)

        # Create the Recording first so file fields are saved and their paths are available
        recording = super().create(validated_data)

        # If a StepConfig was provided, attach it and return
        if provided_step_config:
            recording.step_config = provided_step_config
            recording.save()
            return recording

        # Normalize lists for deterministic ordering
        remove_channels = (
            sorted(recording.remove_channels) if recording.remove_channels else []
        )
        bad_channels = sorted(recording.bad_channels) if recording.bad_channels else []

        # Build a deterministic config block for hashing. Note: we intentionally
        # exclude the creation timestamp so identical recordings hash the same.
        config_block = {
            "function": "recording",
            "bin_file": recording.bin_file.name if recording.bin_file else None,
            "probe_file": recording.probe_file.name if recording.probe_file else None,
            "sampling_rate": recording.sampling_rate,
            "num_channels": recording.num_channels,
            "gain_to_uV": recording.gain_to_uV,
            "offset_to_uV": recording.offset_to_uV,
            "remove_channels": remove_channels,
            "bad_channels": bad_channels,
        }

        # Deterministic JSON string for hashing
        json_text = json.dumps(config_block, sort_keys=True, separators=(",", ":"))
        hash_val = hashlib.sha256(json_text.encode("utf-8")).hexdigest()

        # Get or create the StepConfig
        step_config_obj, created = StepConfig.objects.get_or_create(
            config_block_hash=hash_val, defaults={"config_block": config_block}
        )

        # Link recording to the StepConfig and save
        recording.step_config = step_config_obj
        recording.save()

        return recording
