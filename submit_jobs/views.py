from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from job_queue.models import Job, JobStep, get_or_create_step_configs
from pipeline_factory.models import Pipeline, PipelineStep


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_job_status(request, job_id):
    """
    Retrieve job status and details including all JobSteps and their configurations.
    """
    try:
        job = get_object_or_404(Job, job_id=job_id)
        from .serializers import JobListSerializer

        serializer = JobListSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve job: {str(e)}"},
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
        """Each of these steps has to document in function"""
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

        """Ruben suggested : these needs to be in pipeline and shopuld called from there
        note: Anything which works with database; whether it is fetching steps needs to be in pipeline or in an perticular app!
        Encapsulate all logic related to pipelines within the pipeline app.N
        """
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
                "function": step.config_block_hash.function,
                "identifier": real_identifier,
                "depends": step.depends_on if step.depends_on else [],
            }
            job_steps_data.append(job_step)

        # ========== STEP 6: RESOLVE PLACEHOLDER DEPENDENCIES ==========
        for job_step in job_steps_data:
            if job_step["depends"]:
                resolved_depends = []
                for dep in job_step["depends"]:
                    # Special case: if dependency is a recording placeholder, resolve to current recording hash
                    if dep in ("_RECORDING_", "recording"):
                        resolved_depends.append(recording_identifier)
                    # If this dependency is a placeholder, resolve it to real identifier
                    elif dep in placeholder_to_real_identifier:
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
        from job_queue.models import create_a_job

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_jobs(request):
    """
    List all jobs from qmodel database.
    Returns job summary with status, step counts, and environment info.

    Optional query params:
    - status: Filter by job status (pending, fetched, running, finished, failed)
    - limit: Limit number of results (default: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        from .serializers import JobListSerializer

        # Get query parameters
        status_filter = request.query_params.get("status", None)
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))

        # Query jobs
        jobs_query = Job.objects.all().order_by("-created_at")

        # Apply status filter if provided
        if status_filter:
            jobs_query = jobs_query.filter(status=status_filter)

        # Get total count before pagination
        total_count = jobs_query.count()

        # Apply pagination
        jobs = jobs_query[offset : offset + limit]

        # Serialize
        serializer = JobListSerializer(jobs, many=True)

        return Response(
            {
                "total_count": total_count,
                "count": len(jobs),
                "limit": limit,
                "offset": offset,
                "jobs": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to fetch jobs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_detail(request, job_id):
    """
    Get detailed information about a specific job.
    """
    try:
        from .serializers import JobListSerializer

        job = Job.objects.get(job_id=job_id)
        serializer = JobListSerializer(job)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Job.DoesNotExist:
        return Response(
            {"error": f"Job {job_id} not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch job: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_statistics(request):
    """
    Get job statistics: total jobs, jobs by status, etc.
    """
    try:
        total_jobs = Job.objects.count()

        status_breakdown = {}
        for status_choice in ["pending", "fetched", "running", "finished", "failed"]:
            count = Job.objects.filter(status=status_choice).count()
            status_breakdown[status_choice] = count

        return Response(
            {
                "total_jobs": total_jobs,
                "status_breakdown": status_breakdown,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to fetch statistics: {str(e)}"},
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

        from .serializers import JobListSerializer

        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve jobs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
