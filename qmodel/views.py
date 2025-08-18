# import json
# import hashlib
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.db import transaction
# from django.http import JsonResponse, HttpRequest
# from django.views.decorators.csrf import csrf_exempt
# from rest_framework import viewsets
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import TokenAuthentication
# from .models import Job, JobStep, StepConfig
# from .serializers import JobSerializer
# from datetime import datetime
# from django.contrib import messages


# # ------------------------------
# # API ViewSet for Jobs
# # ------------------------------
# class JobViewSet(viewsets.ModelViewSet):
#     # This queryset now uses the UUID as the unique identifier
#     queryset = Job.objects.all().order_by("-created_at")
#     serializer_class = JobSerializer
#     permission_classes = [IsAuthenticated]


# # ------------------------------
# # Utility function: compute_fingerprint
# # ------------------------------
# def compute_fingerprint(config_block):
#     """
#     Generates a SHA-256 hash (fingerprint) for a given configuration block.
#     Uses json.dumps with sorted keys to ensure a consistent hash for identical content.
#     """
#     json_str = json.dumps(config_block, sort_keys=True)
#     return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


# # ------------------------------
# # View: submit_nested_json_job
# # ------------------------------
# def submit_nested_json_job(request):
#     """
#     Handles the submission of a nested JSON job configuration file.
#     Always creates a new Job with a unique UUID, but reuses existing StepConfig
#     data if the configuration block has been seen before.
#     """
#     if request.method == "POST" and request.FILES.get("json_file"):
#         json_file = request.FILES["json_file"]

#         try:
#             data = json.load(json_file)

#             # --- Extract top-level job details from the JSON ---
#             job_env_config = data.get("job_evn", {})
#             job_steps_list = data.get("job_steps", [])

#             # Basic validation: ensure essential fields are present
#             if not job_steps_list:
#                 raise ValueError("JSON file is missing 'job_steps'.")

#             with transaction.atomic():
#                 # --- Step 1: Process each job step's configuration block ---
#                 step_configs = {}
#                 for step in job_steps_list:
#                     identifier = step.get("identifier")
#                     config_block = data.get(identifier, {})
#                     fingerprint = compute_fingerprint(config_block)
#                     step_configs[identifier] = fingerprint

#                     StepConfig.objects.get_or_create(
#                         config_block_hash=fingerprint,
#                         defaults={"config_block": config_block},
#                     )

#                 # --- Step 2: Create a brand new Job record
#                 job = Job.objects.create(
#                     job_env_config=job_env_config, status="pending"
#                 )

#                 # --- Step 3: Create JobStep records linked to the new Job ---
#                 for step in job_steps_list:
#                     identifier = step.get("identifier")
#                     function = step.get("function")
#                     depends_on = step.get("depends", [])
#                     config_hash = step_configs[identifier]

#                     JobStep.objects.create(
#                         identifier=identifier,
#                         job=job,
#                         function=function,
#                         depends_on=depends_on,
#                         config_block_hash_id=config_hash,
#                         status="pending",
#                     )

#             messages.success(
#                 request, f"✅ Job submitted successfully! ID: {job.job_id}"
#             )
#             return redirect("qmodel:job-list")

#         except json.JSONDecodeError:
#             messages.error(request, "❌ Error: Invalid JSON file format.")
#         except ValueError as e:
#             messages.error(request, f"❌ Error: {str(e)}")
#         except Exception as e:
#             messages.error(request, f"❌ An unexpected error occurred: {str(e)}")

#         return redirect("qmodel:submit_json")

#     jobs = Job.objects.all().order_by("-created_at")
#     return render(request, "qmodel/qmodel_submit_json.html", {"jobs": jobs})


# # ------------------------------
# # View: get_next_job (Updated to handle both GET and POST)
# # ------------------------------
# @api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
# def get_next_job(request: HttpRequest):
#     """
#     API endpoint for a worker to get the next available job (GET) or to update
#     the status of a job/job step (POST).
#     """
#     if request.method == "GET":
#         try:
#             with transaction.atomic():
#                 job_to_process = (
#                     Job.objects.select_for_update()
#                     .filter(status="pending")
#                     .order_by("created_at")
#                     .first()
#                 )

#                 if job_to_process:
#                     job_to_process.status = "fetched"
#                     job_to_process.save()

#                     job_steps = job_to_process.jobstep_set.all()

#                     print(
#                         f"[{datetime.now()}] Job {job_to_process.job_id} fetched by a worker. Status updated to 'fetched'."
#                     )

#                     job_data = {
#                         "job_id": str(job_to_process.job_id),
#                         "job_env_config": job_to_process.job_env_config,
#                         "steps": [
#                             {
#                                 "step_id": str(step.id),
#                                 "identifier": step.identifier,
#                                 "function": step.function,
#                                 "depends_on": step.depends_on,
#                                 "config_block": step.config_block_hash.config_block,
#                             }
#                             for step in job_steps
#                         ],
#                     }
#                     return JsonResponse({"job": job_data}, status=200)

#             return JsonResponse({"message": "No pending jobs found."}, status=404)

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

#     elif request.method == "POST":
#         # This is the logic that was in the 'update_status' view
#         try:
#             data = json.loads(request.body)
#             job_id = data.get("job_id")
#             step_id = data.get("step_id")
#             status = data.get("status")

#             if not job_id or not status:
#                 return JsonResponse(
#                     {"error": "Job ID and status are required."}, status=400
#                 )

#             if step_id:
#                 # Update a specific job step
#                 job_step = get_object_or_404(JobStep, id=step_id, job__job_id=job_id)
#                 job_step.status = status
#                 job_step.save()
#                 return JsonResponse(
#                     {"message": f"Job step {step_id} status updated to {status}."}
#                 )
#             else:
#                 # Update the main job
#                 job = get_object_or_404(Job, job_id=job_id)
#                 job.status = status
#                 job.save()
#                 return JsonResponse(
#                     {"message": f"Job {job_id} status updated to {status}."}
#                 )

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON format."}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


# # ------------------------------
# # View: job_list
# # ------------------------------
# def job_list(request):
#     """
#     Renders a page listing all jobs, ordered by creation date (newest first).
#     """
#     jobs = Job.objects.all().order_by("-created_at")
#     job_steps = (
#         JobStep.objects.all()
#         .select_related("job", "config_block_hash")
#         .order_by("job__created_at", "id")
#     )
#     context = {"jobs": jobs, "job_steps": job_steps}
#     return render(request, "qmodel/job_list.html", context)
import json
import hashlib
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Job, JobStep, StepConfig
from .serializers import JobSerializer
from datetime import datetime


# ------------------------------
# API ViewSet for Jobs
# ------------------------------
class JobViewSet(viewsets.ModelViewSet):
    # This queryset now uses the UUID as the unique identifier
    queryset = Job.objects.all().order_by("-created_at")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


# ------------------------------
# Utility function: compute_fingerprint
# ------------------------------
def compute_fingerprint(config_block):
    """
    Generates a SHA-256 hash (fingerprint) for a given configuration block.
    Uses json.dumps with sorted keys to ensure a consistent hash for identical content.
    """
    json_str = json.dumps(config_block, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


# ------------------------------
# View: submit_nested_json_job
# ------------------------------
def submit_nested_json_job(request):
    """
    Handles the submission of a nested JSON job configuration file.
    Always creates a new Job with a unique UUID, but reuses existing StepConfig
    data if the configuration block has been seen before.
    """
    if request.method == "POST" and request.FILES.get("json_file"):
        json_file = request.FILES["json_file"]

        try:
            data = json.load(json_file)

            # --- Extract top-level job details from the JSON ---
            job_env_config = data.get("job_evn", {})
            job_steps_list = data.get("job_steps", [])

            # Basic validation: ensure essential fields are present
            if not job_steps_list:
                raise ValueError("JSON file is missing 'job_steps'.")

            with transaction.atomic():
                # --- Step 1: Process each job step's configuration block ---
                step_configs = {}
                for step in job_steps_list:
                    identifier = step.get("identifier")
                    config_block = data.get(identifier, {})
                    fingerprint = compute_fingerprint(config_block)
                    step_configs[identifier] = fingerprint

                    StepConfig.objects.get_or_create(
                        config_block_hash=fingerprint,
                        defaults={"config_block": config_block},
                    )

                # --- Step 2: Create a brand new Job record
                # Extract identifier from job_env if available
                job_identifier = job_env_config.get(
                    "identifier", f"job_{str(uuid.uuid4())[:8]}"
                )
                job = Job.objects.create(
                    identifier=job_identifier,
                    job_env_config=job_env_config,
                    status="pending",
                )

                # --- Step 3: Create JobStep records linked to the new Job ---
                for step in job_steps_list:
                    identifier = step.get("identifier")
                    function = step.get("function")
                    depends_on = step.get("depends", [])
                    config_hash = step_configs[identifier]

                    JobStep.objects.create(
                        identifier=identifier,
                        job=job,
                        function=function,
                        depends_on=depends_on,
                        config_block_hash_id=config_hash,
                        status="pending",
                    )

            messages.success(
                request, f"✅ Job submitted successfully! ID: {job.job_id}"
            )
            return redirect("qmodel:qmodel_submit_json")

        except json.JSONDecodeError:
            messages.error(request, "❌ Error: Invalid JSON file format.")
        except ValueError as e:
            messages.error(request, f"❌ Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"❌ An unexpected error occurred: {str(e)}")

        return redirect("qmodel:submit_json")

    jobs = Job.objects.all().order_by("-created_at")
    return render(request, "qmodel/qmodel_submit_json.html", {"jobs": jobs})


# ------------------------------
# View: get_next_job (Updated to handle both GET and POST)
# ------------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def get_next_job(request: HttpRequest):
    """
    API endpoint for a worker to get the next available job (GET) or to update
    the status of a job/job step (POST).
    """
    if request.method == "GET":
        try:
            with transaction.atomic():
                # First, try to get a pending job
                job_to_process = (
                    Job.objects.select_for_update()
                    .filter(status="pending")
                    .order_by("created_at")
                    .first()
                )

                # If no pending jobs, look for fetched jobs that were never processed
                if not job_to_process:
                    job_to_process = (
                        Job.objects.select_for_update()
                        .filter(status="fetched")
                        .order_by("created_at")
                        .first()
                    )

                if job_to_process:
                    # Update status to fetched (or keep it fetched if it was already fetched)
                    old_status = job_to_process.status
                    job_to_process.status = "fetched"
                    job_to_process.save()

                    job_steps = job_to_process.jobstep_set.all()

                    print(
                        f"[{datetime.now()}] Job {job_to_process.job_id} (was {old_status}) fetched by a worker. Status updated to 'fetched'."
                    )

                    job_data = {
                        "job_id": str(job_to_process.job_id),
                        "job_env_config": job_to_process.job_env_config,
                        "steps": [
                            {
                                "step_id": str(step.id),
                                "identifier": step.identifier,
                                "function": step.function,
                                "depends_on": step.depends_on,
                                "config_block": step.config_block_hash.config_block,
                            }
                            for step in job_steps
                        ],
                    }
                    return JsonResponse(job_data, status=200)

            # Return an empty dictionary with a 200 OK status when no jobs are found
            return JsonResponse({}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == "POST":
        # This is the logic that was in the 'update_status' view
        try:
            data = json.loads(request.body)
            job_id = data.get("job_id")
            step_id = data.get("step_id")
            status = data.get("status")

            if not job_id or not status:
                return JsonResponse(
                    {"error": "Job ID and status are required."}, status=400
                )

            if step_id:
                # Update a specific job step
                job_step = get_object_or_404(JobStep, id=step_id, job__job_id=job_id)
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
                return JsonResponse(
                    {"message": f"Job {job_id} status updated to {status}."}
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


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
