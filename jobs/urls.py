from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("create/", views.create_job, name="create_job"),
    path("create-sorting-job/", views.create_sorting_job, name="create_sorting_job"),
    path("status/<str:job_id>/", views.get_job_status, name="get_job_status"),
    path("", views.get_all_jobs, name="get_all_jobs"),
]
