from rest_framework import serializers

from .models import LabNote


class LabNoteSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = LabNote
        fields = ["id", "title", "content", "created_by_username", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by_username", "created_at", "updated_at"]
