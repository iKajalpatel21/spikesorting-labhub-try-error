from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExperimentViewSet,
    submit_json_job,
    get_next_job,  # Renamed from get_pending_job
    list_jobs,
    get_all_jobs,
)

router = DefaultRouter()
router.register(r"experiments", ExperimentViewSet, basename="experiments")

urlpatterns = [
    path("", include(router.urls)),  # /api/experiments/
    path("submit-json/", submit_json_job, name="submit_json"),  # /api/submit-json/
    path(
        "jobs/", get_next_job, name="get_pending_job"
    ),  # /api/experiments/get-next-job/
    path("", list_jobs, name="submit_json"),
    path("api/jobs/", get_all_jobs, name="get_all_jobs"),  # /api/jobs/
]
