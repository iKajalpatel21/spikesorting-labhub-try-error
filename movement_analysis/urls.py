from django.urls import path

from . import views

urlpatterns = [
    path("sessions/",                              views.sessions_list,     name="sessions_list"),
    path("sessions/<int:session_id>/",             views.session_detail,    name="session_detail"),
    path("sessions/<int:session_id>/tracks/",      views.add_track,         name="add_track"),
    path("sessions/<int:session_id>/analysis/",    views.session_analysis,  name="session_analysis"),
    path("analyse/",                               views.analyse_samples,   name="analyse_samples"),
]
