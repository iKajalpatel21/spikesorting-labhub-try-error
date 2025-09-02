"""
Refactored URL configuration with better organization and maintainability.
URLs are now clearly organized and documented.
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views_refactored import JobViewSet
from . import views_refactored as views

app_name = "qmodel"

# =============================================================================
# API Router Configuration
# =============================================================================
router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

# =============================================================================
# URL Patterns
# =============================================================================
urlpatterns = [
    # ==========================================================================
    # Web Interface URLs
    # ==========================================================================
    path(
        "job_list/", 
        views.job_list, 
        name="job_list"
    ),
    path(
        "submit-json/", 
        views.submit_nested_json_job, 
        name="submit_json"
    ),
    
    # ==========================================================================
    # API URLs
    # ==========================================================================
    path(
        "getthenextjob/", 
        views.get_next_job, 
        name="get_next_job"
    ),
    
    # ==========================================================================
    # REST Framework URLs
    # ==========================================================================
    path("", include(router.urls)),
]
