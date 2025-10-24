from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PipelineViewSet, PipelineStepViewSet, RecordingViewSet

router = DefaultRouter()
router.register(r"pipelines", PipelineViewSet, basename="pipeline")
router.register(r"pipeline-steps", PipelineStepViewSet, basename="pipelinestep")
router.register(r"recordings", RecordingViewSet, basename="recording")

urlpatterns = [
    path("", include(router.urls)),
]
