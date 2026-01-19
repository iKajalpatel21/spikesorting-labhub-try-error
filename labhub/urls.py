"""
URL configuration for labhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("qmodel/", include(("qmodel.urls", "qmodel"), namespace="qmodel")),
    path("pipeline/", include("pipeline.urls")),
    path("jobs/", include("jobs.urls")),  # Add jobs routes
    # Serve React app for all non-API routes (must be last)
    re_path(
        r"^(?!admin|qmodel|pipeline|jobs|static).*$",
        TemplateView.as_view(template_name="index.html"),
        name="react-app",
    ),
    # Root path
    path("", TemplateView.as_view(template_name="index.html"), name="react-app-root"),
]

# Serve static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
