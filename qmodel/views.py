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
@csrf_exempt
def submit_nested_json_job(request):
    """
    Handles the submission of a nested JSON job configuration file.
    Always creates a new Job with a unique UUID, but reuses existing StepConfig
    data if the configuration block has been seen before.
    """
    # Added Debugging Statements
    print(f"\n--- DEBUG: POST Request to submit-json ---")
    print(f"Request Method: {request.method}")
    print(f"Request FILES keys: {list(request.FILES.keys())}")
    print(f"Request POST data keys: {list(request.POST.keys())}")
    print(f"-----------------------------------------\n")

    if request.method == "POST" and request.FILES.get("json_file"):
        json_file = request.FILES["json_file"]

        try:
            data = json.load(json_file)
            print(f"\n--- DEBUG: JSON Data Loaded Successfully ---")
            print(json.dumps(data, indent=2))
            print("\n------------------------------------------\n")

            # --- Extract top-level job details from the JSON ---
            job_env_config = data.get("job_evn", {})
            job_steps_list = data.get("job_steps", [])
            version = data.get("version")
            si = data.get("si")

            # Basic validation: ensure essential fields are present
            if not job_steps_list:
                raise ValueError("JSON file is missing 'job_steps'.")

            with transaction.atomic():
                # --- Step 1: Process each job step's configuration block ---
                step_configs = {}
                rebuilt_data = {
                    "version": version,
                    "si": si,
                    "job_evn": job_env_config,
                    "job_steps": job_steps_list,
                }

                for step in job_steps_list:
                    identifier = step.get("identifier")
                    config_block = data.get(identifier, {})
                    fingerprint = compute_fingerprint(config_block)
                    step_configs[identifier] = fingerprint
                    rebuilt_data[identifier] = config_block

                    StepConfig.objects.get_or_create(
                        config_block_hash=fingerprint,
                        defaults={"config_block": config_block},
                    )

                # --- Step 2: Create a brand new Job record
                job = Job.objects.create(
                    job_env_config=job_env_config, status="pending"
                )
                rebuilt_data["job_id"] = str(job.job_id)
                print(f"Job created with ID: {job.job_id}")

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

            # Instead of a redirect, return the full JSON data with the new job ID
            # Check if this is an API request (JSON expected) or web form (HTML expected)
            accept_header = request.META.get('HTTP_ACCEPT', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # If it's a browser request (contains 'text/html'), redirect to HTML page
            if 'text/html' in accept_header or 'Mozilla' in user_agent:
                messages.success(
                    request, f"✅ Job submitted successfully! ID: {job.job_id}"
                )
                return redirect("qmodel:submit_json")
            else:
                # For API requests (curl, worker, etc.), return JSON
                return JsonResponse(rebuilt_data, status=200)

        except json.JSONDecodeError:
            accept_header = request.META.get('HTTP_ACCEPT', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if 'text/html' in accept_header or 'Mozilla' in user_agent:
                messages.error(request, "❌ Error: Invalid JSON file format.")
                return redirect("qmodel:submit_json")
            else:
                return JsonResponse({"error": "Invalid JSON file format."}, status=400)
        except ValueError as e:
            accept_header = request.META.get('HTTP_ACCEPT', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if 'text/html' in accept_header or 'Mozilla' in user_agent:
                messages.error(request, f"❌ Error: {str(e)}")
                return redirect("qmodel:submit_json")
            else:
                return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            accept_header = request.META.get('HTTP_ACCEPT', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            if 'text/html' in accept_header or 'Mozilla' in user_agent:
                messages.error(request, f"❌ An unexpected error occurred: {str(e)}")
                return redirect("qmodel:submit_json")
            else:
                return JsonResponse(
                    {"error": f"An unexpected error occurred: {str(e)}"}, status=500
                )

    # For a GET request, we still want to render the HTML form.
    jobs = Job.objects.all().order_by("-created_at")
    return render(request, "qmodel/qmodel_submit_json.html", {"jobs": jobs})


# ------------------------------
# View: get_next_job (Updated to handle both GET and POST)
# ------------------------------
@api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])  # Temporarily disabled for testing
def get_next_job(request: HttpRequest):
    """
    API endpoint for a worker to get the next available job (GET) or to update
    the status of a job/job step (POST).
    """
    if request.method == "GET":
        try:
            with transaction.atomic():
                job_to_process = (
                    Job.objects.select_for_update()
                    .filter(status="pending")
                    .order_by("created_at")
                    .first()
                )

                if job_to_process:
                    job_to_process.status = "fetched"
                    job_to_process.save()

                    job_steps = job_to_process.jobstep_set.all()

                    # Restructure the data to match the original JSON format
                    rebuilt_data = {
                        "version": "0.4.1",  # Hardcoded for now, can be stored in a config
                        "si": "0.101.0",  # Hardcoded for now
                        "job_id": str(job_to_process.job_id),
                        "job_evn": job_to_process.job_env_config,
                        "job_steps": [],
                    }

                    for step in job_steps:
                        # Append the step dictionary to the job_steps list
                        rebuilt_data["job_steps"].append(
                            {
                                "function": step.function,
                                "identifier": step.identifier,
                                "depends": step.depends_on,
                            }
                        )

                        # Add the configuration block under its identifier key
                        config_block_key = step.identifier
                        rebuilt_data[config_block_key] = (
                            step.config_block_hash.config_block
                        )

                    return JsonResponse(rebuilt_data, status=200)

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


# import json
# import hashlib
# import uuid
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
# @csrf_exempt
# def submit_nested_json_job(request):
#     """
#     Handles the submission of a nested JSON job configuration file.
#     Always creates a new Job with a unique UUID, but reuses existing StepConfig
#     data if the configuration block has been seen before.
#     """
#     # Added Debugging Statements
#     print(f"\n--- DEBUG: POST Request to submit-json ---")
#     print(f"Request Method: {request.method}")
#     print(f"Request FILES keys: {list(request.FILES.keys())}")
#     print(f"Request POST data keys: {list(request.POST.keys())}")
#     print(f"-----------------------------------------\n")

#     if request.method == "POST" and request.FILES.get("json_file"):
#         json_file = request.FILES["json_file"]

#         try:
#             data = json.load(json_file)
#             print(f"\n--- DEBUG: JSON Data Loaded Successfully ---")
#             print(json.dumps(data, indent=2))
#             print("\n------------------------------------------\n")

#             # --- Extract top-level job details from the JSON ---
#             # Handle both "job_env" and "job_evn" (typo in some files)
#             job_env_config = data.get("job_env", data.get("job_evn", {}))
#             job_steps_list = data.get("job_steps", [])
#             version = data.get("version")
#             si = data.get("si")

#             # Basic validation: ensure essential fields are present
#             if not job_steps_list:
#                 raise ValueError("JSON file is missing 'job_steps'.")

#             with transaction.atomic():
#                 # --- Step 1: Process each job step's configuration block ---
#                 step_configs = {}
#                 # Build response in the same order as original JSON
#                 rebuilt_data = {}

#                 # Add fields in original order
#                 if version is not None:
#                     rebuilt_data["version"] = version
#                 if si is not None:
#                     rebuilt_data["si"] = si

#                 # Create job first to get the ID
#                 job = Job.objects.create(
#                     job_env_config=job_env_config, status="pending"
#                 )

#                 # Add job_id right after si (maintaining original position)
#                 rebuilt_data["job_id"] = str(job.job_id)

#                 # Add job_env (using correct field name in response)
#                 rebuilt_data["job_env"] = job_env_config

#                 # Add job_steps
#                 rebuilt_data["job_steps"] = job_steps_list

#                 for step in job_steps_list:
#                     identifier = step.get("identifier")
#                     config_block = data.get(identifier, {})
#                     fingerprint = compute_fingerprint(config_block)
#                     step_configs[identifier] = fingerprint

#                     # Add step config to rebuilt_data in order
#                     rebuilt_data[identifier] = config_block

#                     StepConfig.objects.get_or_create(
#                         config_block_hash=fingerprint,
#                         defaults={"config_block": config_block},
#                     )

#                 # --- Step 2: Job was already created above to get the ID ---
#                 print(f"Job created with ID: {job.job_id}")

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

#             # Instead of a redirect, return the full JSON data with the new job ID
#             print(f"DEBUG: About to return JSON response")
#             print(f"DEBUG: rebuilt_data = {json.dumps(rebuilt_data, indent=2)}")
#             return JsonResponse(rebuilt_data, status=200)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON file format."}, status=400)
#         except ValueError as e:
#             return JsonResponse({"error": str(e)}, status=400)
#         except Exception as e:
#             return JsonResponse(
#                 {"error": f"An unexpected error occurred: {str(e)}"}, status=500
#             )

#     # For a GET request, we still want to render the HTML form.
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
#                     return JsonResponse(job_data, status=200)

#             # Return an empty dictionary with a 200 OK status when no jobs are found
#             return JsonResponse({}, status=200)

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
