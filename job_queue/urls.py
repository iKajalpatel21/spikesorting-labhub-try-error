# qmodel/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import JobViewSet, login, update_status
from . import views

app_name = "job_queue"
router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

urlpatterns = [
    path("job_list/", views.job_list, name="job_list"),
    # Worker API endpoint: GET next job, POST status updates
    # path("getthenextjob/", views.get_next_job, name="get_next_job"),
    path("next-job/", views.get_next_job, name="get_next_job"),
    path("update-status/", update_status, name="update_status"),
    # Authentication endpoint
    path("auth/login/", login, name="login"),
    path("", include(router.urls)),  # REST API routes
]
