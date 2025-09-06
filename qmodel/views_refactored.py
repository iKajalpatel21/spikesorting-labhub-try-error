"""
Refactored Django views with improved structure and maintainability.
All business logic has been extracted to service classes.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Job, JobStep
from .serializers import JobSerializer
from .services.job_service import JobManagementService
from config.constants import ErrorMessages, TemplatePaths

logger = logging.getLogger(__name__)


# =============================================================================
# API ViewSet for Jobs
# =============================================================================
class JobViewSet(viewsets.ModelViewSet):
    """API ViewSet for Job management"""
    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


# =============================================================================
# Job Submission Views
# =============================================================================
@csrf_exempt
def submit_nested_json_job(request):
    """
    Handle JSON job submission with clean error handling and logging
    """
    if request.method == "GET":
        return _render_job_submission_form(request)
    
    if request.method == "POST":
        return _handle_job_submission(request)


def _render_job_submission_form(request):
    """Render the job submission form"""
    jobs = Job.objects.all().order_by("-created_at")
    return render(request, TemplatePaths.SUBMIT_JSON, {"jobs": jobs})


def _handle_job_submission(request):
    """Handle POST request for job submission"""
    # Validate file upload
    if not request.FILES.get("json_file"):
        messages.error(request, "❌ No JSON file provided")
        return redirect("qmodel:submit_json")
    
    json_file = request.FILES["json_file"]
    
    try:
        # Parse JSON data
        data = json.load(json_file)
        logger.debug(f"JSON data loaded successfully for job submission")
        
        # Create job using service
        job = JobManagementService.create_job_from_json(data)
        
        # Success response
        success_message = ErrorMessages.JOB_SUBMITTED_SUCCESS.format(job_id=job.job_id)
        messages.success(request, success_message)
        logger.info(f"Job created successfully: {job.job_id}")
        
        return redirect("qmodel:submit_json")
        
    except json.JSONDecodeError:
        messages.error(request, ErrorMessages.INVALID_JSON)
        logger.error("Invalid JSON format in uploaded file")
    except ValidationError as e:
        messages.error(request, f"❌ Validation Error: {str(e)}")
        logger.error(f"Job validation failed: {e}")
    except Exception as e:
        messages.error(request, f"❌ An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error during job submission: {e}")
    
    return redirect("qmodel:submit_json")


# =============================================================================
# API Endpoints
# =============================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def get_next_job(request: HttpRequest):
    """
    Unified API endpoint for job fetching (GET) and status updates (POST)
    """
    if request.method == "GET":
        return _handle_get_next_job(request)
    elif request.method == "POST":
        return _handle_status_update(request)


def _handle_get_next_job(request: HttpRequest):
    """Handle GET request to fetch next available job"""
    try:
        job = JobManagementService.get_next_pending_job()
        
        if job:
            job_data = JobManagementService.build_job_response(job)
            logger.info(f"Job fetched: {job.job_id}")
            return JsonResponse(job_data, status=200)
        else:
            # No jobs available
            logger.debug("No pending jobs found")
            return JsonResponse({}, status=200)
            
    except Exception as e:
        logger.error(f"Error fetching next job: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def _handle_status_update(request: HttpRequest):
    """Handle POST request to update job/step status"""
    try:
        # Parse request data
        data = json.loads(request.body)
        job_id = data.get("job_id")
        step_id = data.get("step_id")
        status = data.get("status")
        
        # Validate required fields
        if not job_id or not status:
            return JsonResponse(
                {"error": ErrorMessages.JOB_ID_STATUS_REQUIRED}, 
                status=400
            )
        
        if step_id:
            # Update step status
            step = JobManagementService.update_step_status(job_id, step_id, status)
            message = ErrorMessages.JOB_STEP_STATUS_UPDATED.format(
                step_id=step_id, status=status
            )
            logger.info(f"Step status updated: job={job_id}, step={step_id}, status={status}")
        else:
            # Update job status
            job = JobManagementService.update_job_status(job_id, status)
            message = ErrorMessages.JOB_STATUS_UPDATED.format(
                job_id=job_id, status=status
            )
            logger.info(f"Job status updated: job={job_id}, status={status}")
        
        return JsonResponse({"message": message})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in status update request")
        return JsonResponse({"error": ErrorMessages.INVALID_JSON_FORMAT}, status=400)
    except (Job.DoesNotExist, JobStep.DoesNotExist) as e:
        logger.error(f"Job/Step not found in status update: {e}")
        return JsonResponse({"error": "Job or step not found"}, status=404)
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return JsonResponse({"error": str(e)}, status=500)


# =============================================================================
# Display Views
# =============================================================================
def job_list(request):
    """
    Display list of all jobs and their steps
    """
    try:
        jobs = Job.objects.all().order_by("-created_at")
        job_steps = (
            JobStep.objects.all()
            .select_related("job", "config_block_hash")
            .order_by("job__created_at", "id")
        )
        
        context = {
            "jobs": jobs,
            "job_steps": job_steps
        }
        
        return render(request, TemplatePaths.JOB_LIST, context)
        
    except Exception as e:
        logger.error(f"Error loading job list: {e}")
        messages.error(request, f"Error loading job list: {str(e)}")
        return render(request, TemplatePaths.JOB_LIST, {"jobs": [], "job_steps": []})
