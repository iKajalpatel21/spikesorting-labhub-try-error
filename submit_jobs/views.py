import os

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings


def strip_nas_root(path: str) -> str:
    """
    Convert an absolute server path to a $NAS$-prefixed relative path.

    NAS_ROOT marks the NAS mount boundary. Paths under it are stored as
    $NAS$/<relative> so the worker can substitute its own mount prefix.

    Example:
        NAS_ROOT = "/mnt/nas/experiments"
        Input:  "/mnt/nas/experiments/recordings/mouse1/rec.bin"
        Output: "$NAS$/recordings/mouse1/rec.bin"

    If NAS_ROOT is not set or the path does not start with it, the path is
    returned unchanged (safe fallback).
    """
    nas_root = getattr(settings, "NAS_ROOT", "").rstrip("/")
    if nas_root and path and path.startswith(nas_root + "/"):
        return "$NAS$/" + path[len(nas_root) + 1:]
    return path

from job_queue.models import Job, get_or_create_step_configs, create_a_job
from .models import (
    build_job_steps_from_pipeline,
    resolve_placeholder_dependencies,
    build_job_env_config,
)
from .serializers import (
    CreateSortingJobSerializer,
    JobListSerializer,
)


# ============================================================================
# Job Status Endpoint
# ============================================================================


def get_job_status_logic(job_id: str) -> Response:
    """
    Retrieves a single job's full status, including all JobSteps and their configs.

    Args:
        job_id: UUID string of the target Job

    Returns:
        Response: Serialized job data on success, or error message on failure
    """
    try:
        job = get_object_or_404(Job, job_id=job_id)
        serializer = JobListSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve job: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_job_status(request, job_id):
    """
    GET: Retrieve job status and step details for the given job_id.
    """
    return get_job_status_logic(job_id)


# ============================================================================
# Job Creation Endpoint
# ============================================================================


def create_sorting_job_logic(validated_data: dict) -> Response:
    """
    Orchestrates spike-sorting job creation from a validated wizard payload.
    Creates the recording StepConfig, assembles job steps from the pipeline,
    resolves placeholder dependencies, and atomically creates the Job record.

    Args:
        validated_data: Validated dict containing 'recording', 'pipeline_id', 'environment'

    Returns:
        Response: 201 with job_id and step counts on success, 400 on RuntimeError

    Raises:
        RuntimeError: Propagated from create_a_job if job_steps are invalid
    """
    raw = dict(validated_data["recording"])  # Convert OrderedDict to plain dict for JSON serialization
    recording = {
        "binfile":            strip_nas_root(raw["binfile"]),
        "sampling rate":      raw["sampling_rate"],
        "number of channels": raw["num_channels"],
        "gain_to_uV":         raw["gain_to_uV"],
        "offset_to_uV":       raw["offset_to_uV"],
        "probe":              strip_nas_root(raw.get("probe", "")),
        "remove_channels":    raw.get("remove_channels", []),
        "bad_channels":       raw.get("bad_channels", []),
    }
    pipeline_id = validated_data["pipeline_id"]
    environment = validated_data["environment"]

    # Create (or retrieve) the recording StepConfig and get its SHA-256 hash identifier
    recording_identifier = get_or_create_step_configs("recording", recording)

    # Build ordered job steps from the pipeline definition (recording step is prepended)
    job_steps = build_job_steps_from_pipeline(pipeline_id, recording_identifier)

    # Resolve '_RECORDING_' and 'recording' placeholders to the real recording hash
    job_steps = resolve_placeholder_dependencies(job_steps, recording_identifier)

    # Construct the standard job environment configuration
    job_env_config = build_job_env_config(environment)

    # Atomically create the Job and all its JobSteps
    try:
        job = create_a_job(job_env_config, job_steps)
    except RuntimeError as e:
        return Response(
            {"error": f"Failed to create job: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "message": "Job created successfully",
            "job_id": str(job.job_id),
            "recording_identifier": recording_identifier,
            "pipeline_steps_count": len(job_steps) - 1,  # Excludes prepended recording step
            "job_steps_count": len(job_steps),
            "status": "pending",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sorting_job(request):
    """
    POST: Validate React Sorting Job Wizard payload and create a new Job.

    Expected body:
        {
          "recording": {"binfile": "...", "sampling_rate": 30000, "gain_to_uV": 0.195, "offset_to_uV": 0, ...},
          "pipeline_id": 1,
          "environment": "local"
        }
    """
    serializer = CreateSortingJobSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        return create_sorting_job_logic(serializer.validated_data)
    except Exception as e:
        return Response(
            {"error": f"Job creation failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================================
# Job List & Detail Endpoints
# ============================================================================


def list_jobs_logic(status_filter: str | None, limit: int, offset: int) -> Response:
    """
    Queries jobs with optional status filtering and limit/offset pagination.

    Args:
        status_filter: Optional job status to filter by (e.g., 'pending', 'finished')
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip (for pagination)

    Returns:
        Response: Paginated job list with total_count, count, limit, offset, and jobs array
    """
    try:
        jobs_query = Job.objects.all().order_by("-created_at")

        if status_filter:  # Apply status filter only when provided
            jobs_query = jobs_query.filter(status=status_filter)

        total_count = jobs_query.count()  # Count before pagination for accurate total
        jobs = jobs_query[offset : offset + limit]

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
def list_jobs(request):
    """
    GET: List all jobs with optional status filtering and limit/offset pagination.

    Query params:
        status: Filter by job status (pending, fetched, running, finished, failed)
        limit: Max results (default: 100)
        offset: Pagination offset (default: 0)
    """
    status_filter = request.query_params.get("status", None)
    limit = int(request.query_params.get("limit", 100))
    offset = int(request.query_params.get("offset", 0))
    return list_jobs_logic(status_filter, limit, offset)


def job_detail_logic(job_id: str) -> Response:
    """
    Retrieves detailed information for a single job by its UUID.

    Args:
        job_id: UUID string of the target Job

    Returns:
        Response: Serialized job data, 404 if not found, 500 on unexpected error
    """
    try:
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
def job_detail(request, job_id):
    """
    GET: Retrieve full details for a specific job by job_id.
    """
    return job_detail_logic(job_id)


# ============================================================================
# Job Statistics Endpoint
# ============================================================================


def job_statistics_logic() -> Response:
    """
    Computes total job count and a per-status breakdown.

    Returns:
        Response: Dict with total_jobs and status_breakdown counts
    """
    try:
        total_jobs = Job.objects.count()

        status_breakdown = {
            s: Job.objects.filter(status=s).count()
            for s in ["pending", "fetched", "running", "finished", "failed"]
        }  # Count each status in a single comprehension

        return Response(
            {"total_jobs": total_jobs, "status_breakdown": status_breakdown},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to fetch statistics: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_statistics(request):
    """
    GET: Return total job count broken down by status.
    """
    return job_statistics_logic()


# ============================================================================
# All Jobs Endpoint (flat, no pagination)
# ============================================================================


def get_all_jobs_logic(status_filter: str | None) -> Response:
    """
    Retrieves all jobs as a flat list with optional status filtering.

    Args:
        status_filter: Optional job status to filter by

    Returns:
        Response: Flat list of serialized job objects
    """
    try:
        jobs = Job.objects.all().order_by("-created_at")
        if status_filter:  # Apply status filter only when provided
            jobs = jobs.filter(status=status_filter)

        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve jobs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_jobs(request):
    """
    GET: Retrieve all jobs as a flat list, with optional status filter.

    Query params:
        status: Filter by job status (pending, fetched, running, finished, failed)
    """
    return get_all_jobs_logic(request.query_params.get("status"))


# ============================================================================
# Server File Browser Endpoint
# ============================================================================

DATA_FILE_EXTENSIONS = {".bin", ".dat", ".data", ".prb", ".json"}


def _is_safe_path(requested_path, allowed_roots):
    """Return True only if requested_path is inside one of the allowed root directories."""
    requested = os.path.realpath(requested_path)
    return any(
        requested.startswith(os.path.realpath(root.strip()) + os.sep)
        or requested == os.path.realpath(root.strip())
        for root in allowed_roots
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def browse_data_files(request):
    """
    GET: List the immediate contents of a server directory for file browsing.

    Query params:
        path: Directory to list. If omitted, lists the DATA_DIRS roots.

    Response:
        {
          "current_path": "/data/recordings/2024",
          "parents": ["/data/recordings", "/data"],   // breadcrumb chain back to a DATA_DIR root
          "dirs":  [{"name": "session01", "path": "/data/recordings/2024/session01"}, ...],
          "files": [{"name": "rec.bin",   "path": "/data/recordings/2024/rec.bin",
                     "ext": ".bin",       "size_mb": 1234.5}, ...]
        }
    """
    data_dirs = [d.strip() for d in getattr(settings, "DATA_DIRS", []) if d.strip()]
    requested = request.query_params.get("path", "").strip()

    # No path → return the configured root directories as the top level
    if not requested:
        roots = []
        for d in data_dirs:
            roots.append({"name": os.path.basename(d) or d, "path": d})
        return Response(
            {"current_path": None, "parents": [], "dirs": roots, "files": []},
            status=status.HTTP_200_OK,
        )

    # Security: reject any path that escapes the allowed roots
    if not _is_safe_path(requested, data_dirs):
        return Response(
            {"error": "Path is outside the allowed data directories."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not os.path.isdir(requested):
        return Response(
            {"error": f"Not a directory: {requested}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    dirs = []
    files = []
    try:
        entries = sorted(os.scandir(requested), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                dirs.append({"name": entry.name, "path": entry.path})
            elif entry.is_file(follow_symlinks=False):
                ext = os.path.splitext(entry.name)[1].lower()
                if ext in DATA_FILE_EXTENSIONS:
                    try:
                        size_mb = round(entry.stat().st_size / (1024 * 1024), 2)
                    except OSError:
                        size_mb = None
                    files.append({"name": entry.name, "path": entry.path, "ext": ext, "size_mb": size_mb})
    except PermissionError:
        return Response(
            {"error": f"Permission denied reading {requested}"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Build breadcrumb: walk up until we hit a DATA_DIR root
    parents = []
    cursor = os.path.dirname(requested)
    allowed_reals = {os.path.realpath(d) for d in data_dirs}
    while cursor and os.path.realpath(cursor) not in allowed_reals and cursor != os.path.dirname(cursor):
        parents.insert(0, {"name": os.path.basename(cursor) or cursor, "path": cursor})
        cursor = os.path.dirname(cursor)

    return Response(
        {
            "current_path": requested,
            "parents": parents,
            "dirs": dirs,
            "files": files,
        },
        status=status.HTTP_200_OK,
    )
