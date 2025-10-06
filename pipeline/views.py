from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pipeline, PipelineStep
from .serializers import (
    PipelineSerializer,
    PipelineStepSerializer,
    PipelineCreateSerializer,
)


class PipelineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pipelines
    """

    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return PipelineCreateSerializer
        return PipelineSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pipeline = serializer.save()

        # Return the created pipeline with full details
        response_serializer = PipelineSerializer(pipeline)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def steps(self, request, pk=None):
        """Get all steps for a specific pipeline"""
        pipeline = self.get_object()
        steps = pipeline.steps.all()
        serializer = PipelineStepSerializer(steps, many=True)
        return Response(serializer.data)


class PipelineStepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pipeline steps
    """

    queryset = PipelineStep.objects.all()
    serializer_class = PipelineStepSerializer
    permission_classes = [IsAuthenticated]
