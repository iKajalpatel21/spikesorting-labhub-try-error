from django.contrib import admin

from .models import MovementSession, MovementTrack


class MovementTrackInline(admin.TabularInline):
    model = MovementTrack
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(MovementSession)
class MovementSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "created_by", "recorded_at", "updated_at")
    list_filter = ("created_by", "subject")
    search_fields = ("name", "description", "subject")
    inlines = [MovementTrackInline]


@admin.register(MovementTrack)
class MovementTrackAdmin(admin.ModelAdmin):
    list_display = ("label", "session", "created_at")
    list_filter = ("label",)
    search_fields = ("label", "session__name")
