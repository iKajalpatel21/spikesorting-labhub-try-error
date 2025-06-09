from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Experiment
from .serializers import ExperimentSerializer


class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
