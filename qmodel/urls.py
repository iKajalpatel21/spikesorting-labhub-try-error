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
    path("submit-json/", views.submit_nested_json_job, name="submit_json"),
    path("", include(router.urls)),
]
