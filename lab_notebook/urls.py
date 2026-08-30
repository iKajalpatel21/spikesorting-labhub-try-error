from django.urls import path

from . import views

urlpatterns = [
    path("notes/",                        views.notes_list,      name="notes_list"),
    path("notes/<int:note_id>/",          views.note_detail,     name="note_detail"),
    path("notes/<int:note_id>/pdf/",      views.download_pdf,    name="download_pdf"),
    path("notes/<int:note_id>/docx/",     views.download_docx,   name="download_docx"),
    path("notes/<int:note_id>/history/",  views.note_history,    name="note_history"),
    path("transcribe/",                   views.transcribe_audio, name="transcribe_audio"),
]
