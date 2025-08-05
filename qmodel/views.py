from rest_framework import viewsets
from .serializers import JobSerializer
from rest_framework.permissions import IsAuthenticated
import json
import hashlib
from django.shortcuts import render, redirect
from .models import Job, JobStep, JobConfig


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()  # .order_by("id")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


def submit_nested_json_job(request):
    message = ""
    if request.method == "POST" and request.FILES.get("json_file"):
        json_file = request.FILES["json_file"]
        try:
            data = json.load(json_file)

            # STEP 1: Create JobConfig from full raw JSON
            fingerprint = JobConfig.compute_fingerprint(data)
            job_config, created = JobConfig.objects.get_or_create(
                fingerprint=fingerprint,
                defaults={"raw_json": data},
            )

            # STEP 2: Create Job linked to JobConfig
            job = Job.objects.create(config=job_config)

            # STEP 3: Loop through job_steps and store each JobStep
            job_steps = data.get("job_steps", [])
            for step in job_steps:
                identifier = step.get("identifier")
                function = step.get("function")
                depends = step.get("depends", [])

                # Find the config block matching the identifier
                config_block = data.get(identifier, {})

                # Save JobStep
                JobStep.objects.create(
                    job=job,
                    function=function,
                    identifier=identifier,
                    depends_on=depends,
                    config=config_block,
                )

            message = "Job successfully submitted!"

        except Exception as e:
            message = f"Error processing file: {str(e)}"

    # Show all jobs to frontend
    jobs = Job.objects.all()
    return render(
        request,
        "qmodel_submit_json.html",  # Template to render the job submission form
        {"jobs": jobs, "message": message},
    )
