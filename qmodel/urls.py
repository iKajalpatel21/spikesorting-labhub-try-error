# qmodel/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import JobViewSet
from . import views


router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

# urlpatterns = [path("", include(router.urls))]
urlpatterns = [
    path("submit-qmodel/", views.submit_nested_json_job, name="qmodel_submit_json"),
    path("", include(router.urls)),  # ← add this line
]
