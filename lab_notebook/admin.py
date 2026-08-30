from django.contrib import admin

from .models import LabNote, NoteAuditLog


@admin.register(LabNote)
class LabNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at", "updated_at")
    list_filter = ("created_by",)
    search_fields = ("title", "content")


@admin.register(NoteAuditLog)
class NoteAuditLogAdmin(admin.ModelAdmin):
    list_display  = ("note", "action", "user", "timestamp")
    list_filter   = ("action", "user")
    search_fields = ("note__title", "user__username")
    readonly_fields = ("note", "action", "user", "timestamp")

    def has_add_permission(self, request):
        return False   # audit log is append-only

    def has_change_permission(self, request, obj=None):
        return False   # audit log is immutable
