from django.urls import path
from . import views

app_name = "submit_jobs"

urlpatterns = [
    # Specific paths must come BEFORE generic <job_id> pattern
    path("create-sorting-job/", views.create_sorting_job, name="create_sorting_job"),
    path("list/", views.list_jobs, name="list_jobs"),
    path("statistics/", views.job_statistics, name="job_statistics"),
    path("status/<str:job_id>/", views.get_job_status, name="get_job_status"),
    path("browse/", views.browse_data_files, name="browse_data_files"),
    # Generic patterns last
    path("<str:job_id>/", views.job_detail, name="job_detail"),
    path("", views.get_all_jobs, name="get_all_jobs"),
]
