from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import Pipeline, PipelineStep, Recording
from .serializers import (
    PipelineSerializer,
    PipelineStepSerializer,
    PipelineCreateSerializer,
    RecordingSerializer,
)
from qmodel.models import StepConfig
import json
import hashlib


class PipelineViewSet(viewsets.ModelViewSet):
    """ViewSet for listing and creating Pipelines."""

    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Support uploaded JSON that uses the 'job_steps' convention.
        data = request.data
        if (
            isinstance(data, dict)
            and "job_steps" in data
            and isinstance(data["job_steps"], list)
        ):
            job_steps = data["job_steps"]
            steps_array = []
            for js in job_steps:
                identifier = js.get("identifier") or js.get("id")
                base_block = {
                    "function": js.get("function"),
                    "identifier": identifier,
                    "depends": js.get("depends", []),
                }
                keyed = {}
                if (
                    identifier
                    and identifier in data
                    and isinstance(data[identifier], dict)
                ):
                    keyed = data[identifier]
                config_block = {**base_block, **keyed}
                steps_array.append({"config_block": config_block})

            payload = {"description": data.get("description", ""), "steps": steps_array}
        else:
            payload = data

        create_serializer = PipelineCreateSerializer(data=payload)
        create_serializer.is_valid(raise_exception=True)
        pipeline = create_serializer.save()
        out_serializer = PipelineSerializer(pipeline)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class PipelineStepViewSet(viewsets.ModelViewSet):
    """ViewSet for managing pipeline steps"""

    queryset = PipelineStep.objects.all()
    serializer_class = PipelineStepSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class RecordingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Recordings (file uploads + metadata)."""

    queryset = Recording.objects.all()
    serializer_class = RecordingSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Accept the recording form, compute a deterministic config block,
        hash it, and store it directly in qmodel.StepConfig (no Recording row).

        Expected multipart/form-data fields:
        - bin_file (file)
        - probe_file (file)
        - sampling_rate (number)
        - num_channels (int)
        - gain_to_uV (float)
        - offset_to_uV (float)
        - remove_channels (JSON-string or list)
        - bad_channels (JSON-string or list)
        """

        # Helper to parse list fields that may be JSON-encoded strings
        def _parse_list_field(val):
            if val is None:
                return []
            if isinstance(val, list):
                return sorted(val)
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return sorted(parsed)
                except Exception:
                    # Fallback: comma separated values
                    try:
                        parts = [int(p.strip()) for p in val.split(",") if p.strip()]
                        return sorted(parts)
                    except Exception:
                        return []
            return []

        # Extract files (we won't persist them when not creating a Recording)
        bin_file = request.FILES.get("bin_file")
        probe_file = request.FILES.get("probe_file")

        # Extract simple scalar fields
        sampling_rate = request.data.get("sampling_rate")
        num_channels = request.data.get("num_channels")
        gain_to_uV = request.data.get("gain_to_uV")
        offset_to_uV = request.data.get("offset_to_uV")

        # Parse list fields
        remove_channels = _parse_list_field(request.data.get("remove_channels"))
        bad_channels = _parse_list_field(request.data.get("bad_channels"))

        # Build deterministic config block
        config_block = {
            "function": "recording",
            "bin_file": bin_file.name if bin_file else None,
            "probe_file": probe_file.name if probe_file else None,
            "sampling_rate": (
                float(sampling_rate) if sampling_rate not in (None, "") else None
            ),
            "num_channels": (
                int(num_channels) if num_channels not in (None, "") else None
            ),
            "gain_to_uV": float(gain_to_uV) if gain_to_uV not in (None, "") else None,
            "offset_to_uV": (
                float(offset_to_uV) if offset_to_uV not in (None, "") else None
            ),
            "remove_channels": remove_channels,
            "bad_channels": bad_channels,
        }

        # Dev debug: print incoming auth info so we can confirm the header arrives
        try:
            print(
                "DEV-DEBUG: request.META.HTTP_AUTHORIZATION:",
                request.META.get("HTTP_AUTHORIZATION"),
            )
            print(
                "DEV-DEBUG: request.headers.Authorization:",
                request.headers.get("Authorization"),
            )
            print(
                "DEV-DEBUG: request.user.is_authenticated:",
                getattr(request.user, "is_authenticated", False),
            )
        except Exception:
            pass

        # Deterministic JSON string for hashing
        json_text = json.dumps(config_block, sort_keys=True, separators=(",", ":"))
        hash_val = hashlib.sha256(json_text.encode("utf-8")).hexdigest()

        step_config_obj, created = StepConfig.objects.get_or_create(
            config_block_hash=hash_val, defaults={"config_block": config_block}
        )

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {"config_block_hash": hash_val, "created": created}, status=status_code
        )
