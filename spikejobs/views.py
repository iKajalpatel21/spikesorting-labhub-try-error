# from django.shortcuts import render, redirect
# import json
# from rest_framework import viewsets
# from .models import Experiment
# from .serializers import ExperimentSerializer
# from django.urls import reverse
# from django.http import JsonResponse


# def submit_json_job(request):
#     message = request.GET.get("message")
#     error = request.GET.get("error")

#     if request.method == "POST":
#         uploaded_file = request.FILES.get("json_file")
#         if uploaded_file:
#             if not uploaded_file.name.endswith(".json"):
#                 return redirect(
#                     f"{reverse('submit_json')}?error=This+is+not+a+JSON+file."
#                 )
#             try:
#                 data = json.load(uploaded_file)
#                 Experiment.objects.create(
#                     job_type=data.get("job_type", "sorting"),
#                     parameters=json.dumps(data.get("parameters", {})),
#                     status="pending",
#                     priority=data.get("priority", 1),
#                 )
#                 return redirect(
#                     f"{reverse('submit_json')}?message=Job+submitted+successfully!"
#                 )
#             except Exception as e:
#                 return redirect(f"{reverse('submit_json')}?error={str(e)}")

#     return render(request, "submit_json.html", {"message": message, "error": error})


# def get_pending_job(request):
#     if request.method == "GET":
#         job = Experiment.objects.filter(status="pending").first()

#         if job:
#             try:
#                 params = json.loads(job.parameters)
#                 return JsonResponse(
#                     {
#                         "jobid": str(job.id),
#                         "a": params.get("a", 1),
#                         "b": params.get("b", 1),
#                     }
#                 )
#             except Exception as e:
#                 return JsonResponse({"error": str(e)}, status=500)

#         return JsonResponse({})


# class ExperimentViewSet(viewsets.ModelViewSet):
#     queryset = Experiment.objects.all()
#     serializer_class = ExperimentSerializer


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
                    submitted_at=now(),  # optional, if you're tracking time
                )
                return redirect(
                    f"{reverse('submit_json')}?message=Job+submitted+successfully!"
                )
            except Exception as e:
                return redirect(f"{reverse('submit_json')}?error={str(e)}")

    return render(request, "submit_json.html", {"message": message, "error": error})


def get_next_job(request):
    if request.method == "GET":
        job = Experiment.objects.filter(status="pending").first()

        if job:
            try:
                # Mark as fetched
                job.status = "fetched"
                job.save()

                params = json.loads(job.parameters)
                return JsonResponse(
                    {
                        "jobid": str(job.id),
                        "a": params.get("a", 1),
                        "b": params.get("b", 1),
                    }
                )
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        return JsonResponse({})


@csrf_exempt
def update_job_status(request, jobid):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_status = data.get("state")
            job = Experiment.objects.get(id=jobid)

            if new_status in ["running", "finished", "failed"]:
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


def list_jobs(request):
    jobs = Experiment.objects.order_by("-id")  # latest first
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


class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
