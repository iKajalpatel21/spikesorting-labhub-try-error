import json
import hashlib
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages  # Import Django's messaging framework
from .models import Job, JobStep, StepConfig  # Import updated model names
from rest_framework import viewsets
from .serializers import JobSerializer
from rest_framework.permissions import IsAuthenticated


# ------------------------------
# API ViewSet for Jobs
# ------------------------------
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()  # .order_by("id")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


# ------------------------------
# Utility function: compute_fingerprint
# ------------------------------
def compute_fingerprint(config_block):
    """
    Generates a SHA-256 hash (fingerprint) for a given configuration block.
    Uses json.dumps with sorted keys to ensure a consistent hash for identical content,
    regardless of dictionary key order.
    """
    # Convert the Python dictionary config_block into a JSON string with sorted keys
    json_str = json.dumps(config_block, sort_keys=True)
    # Encode the string to bytes (UTF-8 is standard) and then compute the SHA-256 hash
    # .hexdigest() converts the hash into a readable hexadecimal string
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


# ------------------------------
# View: submit_nested_json_job
# ------------------------------
def submit_nested_json_job(request):
    """
    Handles the submission of a nested JSON job configuration file.
    It parses the JSON, creates/updates Job, StepConfig, and JobStep records
    in the database, and provides feedback to the user.
    """
    # Check if the request is a POST request and if a file named 'json_file' was uploaded
    if request.method == "POST" and request.FILES.get("json_file"):
        json_file = request.FILES["json_file"]

        try:
            # Load the JSON data from the uploaded file
            data = json.load(json_file)

            # --- Extract top-level job details from the JSON ---
            # job_id = data.get("job_id")
            job_id = str(uuid.uuid4())  # Generate a UUID if not provided
            job_env_config = data.get(
                "job_evn", {}
            )  # Get job environment config, default to empty dict
            job_steps_list = data.get(
                "job_steps", []
            )  # Get list of job steps, default to empty list

            # Basic validation: ensure essential fields are present
            if not job_id:
                raise ValueError("JSON file is missing 'job_id'.")
            if not job_steps_list:
                raise ValueError("JSON file is missing 'job_steps'.")

            # --- Step 1: Process each job step's configuration block ---
            # This phase ensures all unique configuration blocks are stored in StepConfig
            # before JobSteps attempt to link to them.
            step_configs = (
                {}
            )  # Dictionary to store {step_identifier: config_hash} mappings
            for step in job_steps_list:
                identifier = step.get("identifier")
                # Get the specific configuration block for this step from the main JSON data
                config_block = data.get(identifier, {})

                # Compute the unique SHA-256 fingerprint for this config block
                fingerprint = compute_fingerprint(config_block)
                step_configs[identifier] = fingerprint  # Store the hash for later use

                # Use get_or_create to add the config block to StepConfig if it's new,
                # or retrieve it if it already exists. This prevents duplicates.
                StepConfig.objects.get_or_create(
                    config_block_hash=fingerprint,  # Use the hash as the primary key for lookup/creation
                    defaults={
                        "config_block": config_block
                    },  # The actual JSON data to store if new
                )
                # DB>>
                # conf_fromdb = StepConfig.objects.get("config_block")
                print(
                    f"config:\n. {step}\n {identifier}\n {fingerprint}\n {config_block}"
                )

                # print(f"config_block:{config_block}")
                # <<DB

            # --- Step 2: Create or retrieve the main Job record ---
            # We use get_or_create to prevent re-submitting an identical job.
            # 'created' will be True if a new Job was made, False if it already existed.
            job, created = Job.objects.get_or_create(
                job_id=job_id,
                defaults={"job_env_config": job_env_config, "status": "pending"},
            )

            # --- Step 3: Create JobStep records, but only if the main Job is new ---
            if created:
                # Loop through each step definition from the JSON
                for step in job_steps_list:
                    identifier = step.get("identifier")
                    function = step.get("function")
                    depends_on = step.get("depends", [])

                    # Retrieve the config hash (fingerprint) that we stored earlier
                    config_hash = step_configs[identifier]

                    # Create a new JobStep record.
                    # 'job=job' links this step to the Job object we just created/retrieved.
                    # 'config_block_hash_id=config_hash' links this step to the StepConfig
                    # using the hash as the foreign key value, avoiding an extra DB query.
                    JobStep.objects.create(
                        identifier=identifier,
                        job=job,  # Link to the Job instance
                        function=function,
                        depends_on=depends_on,
                        config_block_hash_id=config_hash,  # Link to the StepConfig by its hash
                        status="pending",
                    )
                # Add a success message to be displayed on the next page
                messages.success(request, f"✅ Job '{job_id}' successfully submitted!")
            else:
                # Add an info message if the job already existed
                messages.info(
                    request,
                    f"ℹ️ Job with ID '{job_id}' already exists. No new steps were created.",
                )

            # Redirect the user to the job list page after processing the POST request.
            # This prevents accidental re-submission if the user refreshes.
            return redirect("qmodel:job_list")

        except json.JSONDecodeError:
            # Handle cases where the uploaded file is not valid JSON
            messages.error(request, "❌ Error: Invalid JSON file format.")
            return redirect("qmodel:job_list")
        except ValueError as e:
            # Handle custom validation errors (e.g., missing job_id)
            messages.error(request, f"❌ Error: {str(e)}")
            return redirect("qmodel:job_list")
        except Exception as e:
            # Catch any other unexpected errors during processing
            messages.error(request, f"❌ An unexpected error occurred: {str(e)}")
            return redirect("qmodel:job_list")

    # --- Handle GET requests (or if POST request failed before redirect) ---
    # Retrieve all existing jobs from the database, ordered by creation date (newest first)
    jobs = Job.objects.all().order_by("-created_at")
    # Render the HTML template, passing the list of jobs and any messages
    return render(request, "qmodel/qmodel_submit_json.html", {"jobs": jobs})


# ------------------------------
# View: job_list
# ------------------------------
def job_list(request):
    """
    Renders a page listing all jobs, ordered by creation date (newest first).
    This view is required for redirects after job submission.
    """
    # Fetch all jobs, ordered by creation date (newest first).
    jobs = Job.objects.all().order_by("-created_at")

    # Fetch all job steps, and pre-fetch related Job and StepConfig objects
    job_steps = (
        JobStep.objects.all()
        .select_related("job", "config_block_hash")
        .order_by("job__created_at", "id")
    )

    # Add print statements to display the retrieved data in the terminal
    print("\n--- Job Steps retrieved from the database ---")
    for step in job_steps:
        # Access the related StepConfig object via the foreign key
        config = step.config_block_hash

        print(f"JobStep Identifier: {step.identifier}")
        print(f"Function: {step.function}")
        print(f"Config Hash: {config.config_block_hash}")
        print(f"Config Block: {config.config_block}")
        print("-" * 20)  # Separator for readability

    print("----------------------------------------\n")

    context = {"jobs": jobs, "job_steps": job_steps}

    return render(request, "qmodel/job_list.html", {"jobs": jobs})
