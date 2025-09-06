# qmodel/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import JobViewSet
from . import views

app_name = "qmodel"
router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

# urlpatterns = [path("", include(router.urls))]
urlpatterns = [
    path("job_list/", views.job_list, name="job_list"),
    # Existing URL for submitting a job
    path("submit-json/", views.submit_nested_json_job, name="submit_json"),
    # Official dummy worker API endpoints
    path("next-job/", views.get_next_job_official, name="next_job_official"),
    path("status/", views.update_job_status_official, name="update_status_official"),
    # Legacy endpoint (for backward compatibility)
    path("getthenextjob/", views.get_next_job, name="get_next_job"),
    path("", include(router.urls)),  # Existing router URLs
]
