from django.shortcuts import render, redirect
import json
from rest_framework import viewsets
from .models import Experiment
from .serializers import ExperimentSerializer
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.serializers import serialize
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator


# --------------------------------------------------------------------
# View: Submit JSON Job via POST Form
# --------------------------------------------------------------------
def submit_json_job(request):
    message = request.GET.get("message")
    error = request.GET.get("error")

    if request.method == "POST":
        uploaded_file = request.FILES.get("json_file")
        if uploaded_file:
            if not uploaded_file.name.endswith(".json"):
                return redirect(
                    f"{reverse('submit_json')}?error=This+is+not+a+JSON+file."
                )
            try:
                data = json.load(uploaded_file)
                Experiment.objects.create(
                    job_type=data.get("job_type", "sorting"),
                    parameters=json.dumps(data.get("parameters", {})),
                    status="pending",
                    priority=data.get("priority", 1),
                    submitted_at=now(),  # Optional timestamp
                )
                return redirect(
                    f"{reverse('submit_json')}?message=Job+submitted+successfully!"
                )
            except Exception as e:
                return redirect(f"{reverse('submit_json')}?error={str(e)}")

    return render(request, "submit_json.html", {"message": message, "error": error})


# --------------------------------------------------------------------
# View: Update Job Status via POST
# --------------------------------------------------------------------
@csrf_exempt
def update_job_status(request, jobid):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_status = data.get("state")
            job = Experiment.objects.get(id=jobid)

            if new_status in ["fetched", "running", "finished", "failed"]:
                job.status = new_status
                job.save()
                return JsonResponse({"message": f"Job {jobid} updated to {new_status}"})
            else:
                return JsonResponse({"error": "Invalid state"}, status=400)

        except Experiment.DoesNotExist:
            return JsonResponse({"error": "Job not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# --------------------------------------------------------------------
# View: List All Jobs for Display in HTML Template
# --------------------------------------------------------------------
def list_jobs(request):
    jobs = Experiment.objects.order_by("-id")  # Latest first
    job_data = []

    for job in jobs:
        try:
            params = json.loads(job.parameters)
        except:
            params = {}
        job_data.append(
            {
                "id": job.id,
                "status": job.status,
                "a": params.get("a", ""),
                "b": params.get("b", ""),
                "priority": job.priority,
            }
        )

    return render(
        request,
        "submit_json.html",
        {
            "jobs": job_data,
            "message": request.GET.get("message"),
            "error": request.GET.get("error"),
        },
    )


# --------------------------------------------------------------------
# API View: Return All Jobs in JSON Format (for external fetch)
# --------------------------------------------------------------------
@require_GET
def get_all_jobs(request):
    jobs = Experiment.objects.all().order_by("-id")
    job_data = []

    for job in jobs:
        try:
            params = json.loads(job.parameters)
        except:
            params = {}
        job_data.append(
            {
                "id": job.id,
                "status": job.status,
                "a": params.get("a"),
                "b": params.get("b"),
                "priority": job.priority,
            }
        )

    return JsonResponse(job_data, safe=False)


# --------------------------------------------------------------------
# ViewSet: DRF ModelViewSet for Experiments
# --------------------------------------------------------------------
# @method_decorator(csrf_exempt, name="dispatch")          # ← NEW – kills CSRF 403s
# class ExperimentViewSet(viewsets.ModelViewSet):
#     queryset = Experiment.objects.all()
#     serializer_class = ExperimentSerializer

#     @action(detail=False, methods=["get"], url_path="get-next")
#     def get_next_job(self, request):
#         try:
#             with transaction.atomic():
#                 job = (
#                     Experiment.objects.select_for_update(skip_locked=True)
#                     .filter(status="pending")
#                     .order_by("id")
#                     .first()
#                 )

#                 if job:
#                     # ✅ Immediately update the job to 'fetched'
#                     job.status = "fetched"
#                     job.save()

#                     # ✅ Parse parameters and return to worker
#                     params = json.loads(job.parameters)
#                     return Response(
#                         {
#                             "id": job.id,
#                             "parameters": params,
#                         },
#                         status=status.HTTP_200_OK,
#                     )

#             # No pending jobs
#             return Response({}, status=status.HTTP_204_NO_CONTENT)


#         except Exception as e:
#             return Response(
#                 {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@method_decorator(csrf_exempt, name="dispatch")  # ← NEW – kills CSRF 403s
class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer

    # --- worker pulls the next pending job -------------
    @action(detail=False, methods=["get"], url_path="get-next")
    def get_next(self, request):
        with transaction.atomic():
            job = (
                Experiment.objects.select_for_update(skip_locked=True)
                .filter(status="pending")
                .order_by("id")
                .first()
            )
            if not job:
                return Response({}, status=status.HTTP_204_NO_CONTENT)

            job.status = "fetched"
            job.save()

            return Response(
                {"id": job.id, "parameters": json.loads(job.parameters)},
                status=status.HTTP_200_OK,
            )

    # --- DRF’s PATCH endpoint needs no code, but we must leave it CSRF‑free
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
