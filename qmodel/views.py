import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpRequest
from django.contrib.auth import authenticate
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from .models import Job, JobStep, StepConfig, get_next_job_id
from .serializers import JobSerializer


# ============================================================================
# API ViewSet for Jobs
# ============================================================================


class JobViewSet(viewsets.ModelViewSet):
    """
    REST API ViewSet for Job management.
    Provides CRUD operations for Job objects.
    """

    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


# ============================================================================
# Worker API Endpoints
# ============================================================================


def get_job() -> dict:
    job_to_process = get_next_job_id()
    if job_to_process is None:
        return {}
    job_data = {
        "version": "0.4.1",  # Added version aug27
        "si": "0.101.0",  # Added si aug27
    }
    job_data["job_id"] = str(job_to_process.job_id)
    job_data["job_evn"] = job_to_process.job_env_config  # Use "job_evn" to match spec

    job_steps = job_to_process.jobstep_set.all()
    job_data["job_steps"] = [
        {
            "function": step.function,
            "identifier": step.identifier,
            "depends": step.depends_on,  # Use "depends" to match spec
        }
        for step in job_steps
    ]
    for step in job_steps:
        job_data[step.identifier] = step.config_block_hash.config_block
    return job_data


def update_job_status(data: dict) -> JsonResponse:
    """
    Updates job or job step status based on provided data.

    Args:
        data: Dictionary containing job_id, optional step_id, and status

    Returns:
        JsonResponse: Success or error message
    """
    job_id = data.get("job_id", None)
    step_id = data.get("step_id", None)
    status = data.get("status", None)

    if job_id is None or status is None:
        return JsonResponse({"error": "Job ID and status are required."}, status=400)

    if step_id:
        # Update a specific job step - use identifier field, not id field
        job_step = get_object_or_404(JobStep, identifier=step_id, job__job_id=job_id)
        job_step.status = status
        job_step.save()
        return JsonResponse(
            {"message": f"Job step {step_id} status updated to {status}."}
        )
    else:
        # Update the main job
        job = get_object_or_404(Job, job_id=job_id)
        job.status = status
        job.save()
        return JsonResponse({"message": f"Job {job_id} status updated to {status}."})


# ============================================================================
# Worker API Endpoints - Helper Functions
# ============================================================================


def next_job_get_logic() -> JsonResponse:
    """
    GET handler for worker job assignment.
    Fetches the next pending job and returns its details.

    Returns:
        JsonResponse: Job data with all steps and configurations, or empty dict if none available
    """
    try:
        job_data = get_job()
        return JsonResponse(job_data, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def next_job_post_logic(request: HttpRequest) -> JsonResponse:
    """
    POST handler for worker job/step status updates.
    Updates job or individual step status based on the request data.

    Args:
        request: HTTP request containing job_id, optional step_id, and status

    Returns:
        JsonResponse: Success or error message
    """
    try:
        data = json.loads(request.body)
        return update_job_status(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Endpoint: get_next_job (GET/POST)
# Handles worker requests for job assignments and status updates
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def get_next_job(request: HttpRequest):
    """
    Worker API Endpoint - Get next job and update job/step status.

    GET: Fetch the next pending job for the worker
    POST: Update job or job step status
    """
    if request.method == "GET":
        return next_job_get_logic()
    elif request.method == "POST":
        return next_job_post_logic(request)


# ------------------------------
# View: job_list
# ------------------------------
def job_list(request):
    """
    Renders a page listing all jobs, ordered by creation date (newest first).
    """
    jobs = Job.objects.all().order_by("-created_at")
    job_steps = (
        JobStep.objects.all()
        .select_related("job", "config_block_hash")
        .order_by("job__created_at", "id")
    )
    context = {"jobs": jobs, "job_steps": job_steps}
    return render(request, "qmodel/job_list.html", context)


# ============================================================================
# Authentication Endpoint
# ============================================================================


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user with username and password.
    Returns token and user info on success.
    """
    from rest_framework.authtoken.models import Token

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return JsonResponse(
            {"detail": "Username and password are required."},
            status=400,
        )

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse(
            {"detail": "Invalid credentials."},
            status=401,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return JsonResponse(
        {
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
        },
        status=200,
    )


# ============================================================================
# Job Creation Endpoint
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_job(request):
    """
    Create a new job from wizard submission.

    Expects JSON payload with:
    - recording: Recording configuration (binfile, probeFile, samplingRate, etc.)
    - pipeline_id: Selected pipeline ID
    - job_env_preset: Environment preset (e.g., 'default')

    Returns job_id and job_env_config
    """
    import uuid
    from django.conf import settings

    try:
        data = request.data

        # Extract recording and pipeline info
        recording = data.get("recording", {})
        pipeline_id = data.get("pipeline_id")
        job_env_preset = data.get("job_env_preset", "default")

        # Validate required fields
        if not recording:
            return JsonResponse({"error": "Recording data is required."}, status=400)
        if not pipeline_id:
            return JsonResponse({"error": "Pipeline ID is required."}, status=400)

        # Generate job_id
        job_id = uuid.uuid4()

        # Generate default environment config using template
        job_env_config = _generate_job_env_config(
            job_id=job_id, preset=job_env_preset, recording=recording
        )

        # Create Job record
        job = Job.objects.create(
            job_id=job_id, job_env_config=job_env_config, status="pending"
        )

        return JsonResponse(
            {
                "job_id": str(job_id),
                "job_env_config": job_env_config,
                "status": "created",
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def _generate_job_env_config(job_id, preset, recording):
    """
    Generate job environment config from template.

    Args:
        job_id: UUID of the job
        preset: Environment preset (e.g., 'default')
        recording: Recording configuration dict

    Returns:
        dict: job_env configuration
    """
    # Extract recording directory (can be from binfile path or provided)
    recording_dir = recording.get("recording_dir", f"/tmp/recording_{job_id}")

    # Default environment template
    job_env_config = {
        "base_directory": f"$LOCAL$/{job_id}",
        "job_kwargs": {
            "n_jobs": 40,
            "total_memory": "128G",
            "chunk_duration": "60s",
            "progress_bar": True,
        },
        "log_level": "DEBUG",
        "REDIRECT": {
            "log": f"{recording_dir}/{job_id}/run.log",
            "out": f"{recording_dir}/{job_id}/run.out",
            "err": f"{recording_dir}/{job_id}/run.err",
        },
    }

    return job_env_config
