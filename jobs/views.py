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
        pipeline = get_object_or_404(Pipeline, id=pipeline_id)

        # All operations happen in a single transaction
        with transaction.atomic():
            # ============================================================
            # STEP 1: Create Job first (to get job_id)
            # ============================================================
            job = Job.objects.create(job_env_config=job_env_preset, status="pending")

            job_steps_list = []
            dependencies_map = {}  # Track hashes for dependency injection

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

            # ============================================================
            # STEP 4: Fetch pipeline templates
            # ============================================================
            pipeline_steps = PipelineStep.objects.filter(pipeline=pipeline).order_by(
                "order"
            )

            # Build template order: preprocessing → sorting → analyzer → phy_export → upload
            # (skip recording as it was already created)
            previous_hash = recording_hash

            for pipeline_step in pipeline_steps:
                step_function = pipeline_step.function
                step_config = pipeline_step.config or {}

                # ============================================================
                # STEPS 5-8: Create StepConfigs and JobSteps with dependencies
                # ============================================================

                # Get or create the StepConfig
                step_hash = get_or_create_step_configs(step_function, step_config)
                dependencies_map[step_function] = step_hash

                # Determine dependencies based on step type
                if step_function == "preprocessing":
                    # Preprocessing depends on recording
                    depends_on = [recording_hash]
                elif step_function == "sorting":
                    # Sorting depends on preprocessing
                    depends_on = [dependencies_map.get("preprocessing")]
                elif step_function == "analyzer":
                    # Analyzer depends on preprocessing AND sorting
                    depends_on = [
                        dependencies_map.get("preprocessing"),
                        dependencies_map.get("sorting"),
                    ]
                elif step_function == "phy_export":
                    # Phy export depends on preprocessing AND sorting
                    depends_on = [
                        dependencies_map.get("preprocessing"),
                        dependencies_map.get("sorting"),
                    ]
                elif step_function == "upload":
                    # Upload can depend on analyzer and phy_export
                    depends_on = [
                        dependencies_map.get("analyzer"),
                        dependencies_map.get("phy_export"),
                    ]
                else:
                    # Custom steps depend on previous step
                    depends_on = [previous_hash]

                # Clean up None values from depends_on
                depends_on = [dep for dep in depends_on if dep is not None]

                # Create JobStep with injected dependencies
                job_step = JobStep.objects.create(
                    job=job,
                    identifier=step_hash,
                    function=step_function,
                    depends_on=depends_on,
                    config_block_hash_id=step_hash,
                    status="pending",
                )
                job_steps_list.append(job_step)
                previous_hash = step_hash

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
