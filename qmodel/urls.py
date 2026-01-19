# qmodel/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import JobViewSet, login, create_job
from . import views

app_name = "qmodel"
router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

urlpatterns = [
    path("job_list/", views.job_list, name="job_list"),
    # Worker API endpoint: GET next job, POST status updates
    path("getthenextjob/", views.get_next_job, name="get_next_job"),
    # Job creation endpoint
    path("jobs/create/", create_job, name="create_job"),
    # Authentication endpoint
    path("auth/login/", login, name="login"),
    path("", include(router.urls)),  # REST API routes
]
