from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from qmodel.models import Job, JobStep, get_or_create_step_configs, compute_fingerprint
from pipeline.models import Pipeline, PipelineStep
from .models import JobCreationLog
from .serializers import JobSerializer, JobCreationLogSerializer
from .step_config import get_step_dependencies, validate_dependencies


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job(request):
    """
    Complete job creation endpoint following the step-by-step flow:

    Step 0: Receive single request with:
        - pipeline_id: ID of the pipeline to use
        - recording_config: Recording configuration block
        - job_env_preset: Job environment configuration

    Steps 1-9: Execute atomically in backend
        1. Create Job
        2. Create recording StepConfig, get hash
        3. Create recording JobStep with no dependencies
        4. Fetch pipeline templates
        5-8. Create remaining steps with dependencies injected
        9. Commit transaction
    """

    try:
        # Validate request data
        data = request.data
        pipeline_id = data.get("pipeline_id")
        recording_config = data.get("recording_config")
        job_env_preset = data.get("job_env_preset")

        if not all([pipeline_id, recording_config, job_env_preset]):
            return Response(
                {
                    "error": "Missing required fields: pipeline_id, recording_config, job_env_preset"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate pipeline exists
        pipeline = get_object_or_404(Pipeline, pipeline_id=pipeline_id)

        # All operations happen in a single transaction
        with transaction.atomic():
            # ============================================================
            # STEP 1: Create Job first (to get job_id)
            # ============================================================
            job = Job.objects.create(job_env_config=job_env_preset, status="pending")

            job_steps_list = []
            dependencies_map = {}  # Track hashes for dependency injection
            available_steps = {}  # Track all steps for dependency resolution

            # ============================================================
            # STEP 2-3: Create recording StepConfig and JobStep
            # ============================================================
            recording_hash = get_or_create_step_configs("recording", recording_config)
            dependencies_map["recording"] = recording_hash

            # Create recording JobStep with no dependencies
            recording_step = JobStep.objects.create(
                job=job,
                identifier=recording_hash,
                function="recording",
                depends_on=[],  # Recording has no dependencies
                config_block_hash_id=recording_hash,
                status="pending",
            )
            job_steps_list.append(recording_step)

            # Add recording to available steps for dependency resolution
            available_steps[recording_hash] = {
                "function": "recording",
                "identifier": recording_hash,
            }

            # ============================================================
            # STEP 4: Fetch pipeline templates
            # ============================================================
            pipeline_steps = PipelineStep.objects.filter(pipeline=pipeline).order_by(
                "order"
            )

            for pipeline_step in pipeline_steps:
                step_function = pipeline_step.function
                step_config = pipeline_step.config or {}

                # ============================================================
                # STEPS 5-8: Create StepConfigs and JobSteps with dependencies
                # ============================================================

                # Get or create the StepConfig
                step_hash = get_or_create_step_configs(step_function, step_config)
                dependencies_map[step_function] = step_hash

                # Build available steps map for dependency resolution
                available_steps[step_hash] = {
                    "function": step_function,
                    "identifier": step_hash,
                }

                # Get required dependencies from STEP_DEPENDENCIES spec
                required_dep_slots = get_step_dependencies(step_function)

                if not required_dep_slots:
                    # No dependencies required
                    depends_on = []
                else:
                    # Resolve dependencies based on spec
                    # For each required dependency slot, find a matching previous step
                    depends_on = []
                    for slot_idx, required_funcs in enumerate(required_dep_slots):
                        # required_funcs is a tuple of acceptable function types
                        if isinstance(required_funcs, str):
                            required_funcs = (required_funcs,)

                        # Find the most recent step of acceptable type
                        found_dep = None
                        for prev_step_hash in reversed(list(available_steps.keys())):
                            if prev_step_hash == step_hash:
                                continue  # Skip self
                            prev_step_func = available_steps[prev_step_hash]["function"]
                            if prev_step_func in required_funcs:
                                found_dep = prev_step_hash
                                break

                        if found_dep:
                            depends_on.append(found_dep)
                        else:
                            # No matching previous step found
                            raise ValueError(
                                f"Cannot find dependency for {step_function} slot {slot_idx + 1}. "
                                f"Need one of: {required_funcs}"
                            )

                # Create JobStep with proper dependencies from spec
                job_step = JobStep.objects.create(
                    job=job,
                    identifier=step_hash,
                    function=step_function,
                    depends_on=depends_on,
                    config_block_hash_id=step_hash,
                    status="pending",
                )
                job_steps_list.append(job_step)

            # ============================================================
            # STEP 9: Transaction commits automatically at end of with block
            # ============================================================

            # Log the job creation
            log = JobCreationLog.objects.create(
                job=job,
                pipeline_id=pipeline_id,
                recording_config=recording_config,
                job_env_preset=job_env_preset,
                status="success",
            )

        # Return success response
        serializer = JobSerializer(job)
        return Response(
            {
                "message": "Job created successfully",
                "job": serializer.data,
                "job_id": str(job.job_id),
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        # Log failed job creation
        try:
            JobCreationLog.objects.create(
                pipeline_id=request.data.get("pipeline_id", None),
                recording_config=request.data.get("recording_config", {}),
                job_env_preset=request.data.get("job_env_preset", {}),
                status="failed",
                error_message=str(e),
            )
        except:
            pass

        return Response(
            {"error": f"Failed to create job: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_job_status(request, job_id):
    """
    Retrieve job status and details including all JobSteps and their configurations.
    """
    try:
        job = get_object_or_404(Job, job_id=job_id)
        serializer = JobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve job: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_jobs(request):
    """
    Retrieve all jobs with pagination and filtering.
    """
    try:
        # Optional filters
        status_filter = request.query_params.get("status")

        jobs = Job.objects.all()
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        jobs = jobs.order_by("-created_at")

        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve jobs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sorting_job(request):
    """
    STEP 1: Validate React Sorting Job Wizard Payload
    STEP 2: Create recording config in qmodel StepConfig

    Input from React:
    {
      "recording": {
        "binfile": "/path/to/recording.bin",
        "sampling_rate": 30000,
        "num_channels": 32,
        "gain": 0.195,
        "offset": 0,
        "probe": "/path/to/probe.json"
      },
      "pipeline_id": 1,
      "environment": "local"
    }
    """
    from .serializers import CreateSortingJobSerializer

    try:
        # ========== STEP 1: VALIDATE REQUEST ==========
        serializer = CreateSortingJobSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        recording = validated_data["recording"]
        pipeline_id = validated_data["pipeline_id"]
        environment = validated_data["environment"]

        # ========== STEP 2: CREATE RECORDING CONFIG IN QMODEL ==========
        # Convert OrderedDict to dict for JSON serialization
        recording_config = dict(recording)

        # Create recording StepConfig and get its identifier (SHA-256 hash)
        recording_identifier = get_or_create_step_configs("recording", recording_config)

        # ========== STEP 3: LOAD PIPELINE STEPS ==========
        pipeline = Pipeline.objects.get(pipeline_id=pipeline_id)
        pipeline_steps = PipelineStep.objects.filter(pipeline=pipeline).order_by(
            "pipeline_step_id"
        )

        # ========== STEP 4-5: USE EXISTING STEPCONFIGS FROM PIPELINE ==========
        # NOTE: StepConfigs were already created when the pipeline was submitted.
        # We just reference them here instead of recreating.
        job_steps_data = []
        placeholder_to_real_identifier = {}  # Map placeholders to real identifiers

        # Add recording step first
        recording_step = {
            "function": "recording",
            "identifier": recording_identifier,
            "depends": [],
        }
        job_steps_data.append(recording_step)

        # Add pipeline steps and build identifier mapping
        for step in pipeline_steps:
            # Use the config_block_hash that was already created when pipeline was submitted
            real_identifier = step.config_block_hash.config_block_hash

            # Store original placeholder -> real identifier mapping
            placeholder_to_real_identifier[step.config_block_hash.config_block_hash] = (
                real_identifier
            )

            job_step = {
                "function": step.function,
                "identifier": real_identifier,
                "depends": step.depends_on if step.depends_on else [],
            }
            job_steps_data.append(job_step)

        # ========== STEP 6: RESOLVE PLACEHOLDER DEPENDENCIES ==========
        for job_step in job_steps_data:
            if job_step["depends"]:
                resolved_depends = []
                for dep in job_step["depends"]:
                    # If this dependency is a placeholder, resolve it to real identifier
                    if dep in placeholder_to_real_identifier:
                        resolved_depends.append(placeholder_to_real_identifier[dep])
                    else:
                        # If already a real identifier or special case, keep as is
                        resolved_depends.append(dep)
                job_step["depends"] = resolved_depends

        # ========== STEP 7: BUILD JOB ENVIRONMENT ==========
        job_env_config = {
            "base_directory": "/tmp/spike_sorting",
            "job_kwargs": {"environment": environment},
            "log_level": "INFO",
            "REDIRECT": True,
        }

        # ========== STEP 8: CREATE JOB AND JOBSTEPS USING QMODEL FUNCTIONS ==========
        from qmodel.models import create_a_job

        try:
            job = create_a_job(job_env_config, job_steps_data)

            return Response(
                {
                    "message": "Job created successfully",
                    "job_id": str(job.job_id),
                    "recording_identifier": recording_identifier,
                    "pipeline_steps_count": pipeline_steps.count(),
                    "job_steps_count": len(job_steps_data),
                    "status": "pending",
                },
                status=status.HTTP_201_CREATED,
            )
        except RuntimeError as e:
            return Response(
                {"error": f"Failed to create job: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response(
            {"error": f"Job creation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
