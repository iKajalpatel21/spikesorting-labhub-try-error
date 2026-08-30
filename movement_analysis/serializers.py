from rest_framework import serializers

from .models import MovementSession, MovementTrack


class MovementTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovementTrack
        fields = ["id", "label", "samples", "created_at"]
        read_only_fields = ["id", "created_at"]


class MovementSessionSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    tracks = MovementTrackSerializer(many=True, read_only=True)

    class Meta:
        model = MovementSession
        fields = [
            "id",
            "name",
            "description",
            "subject",
            "recorded_at",
            "sample_rate_hz",
            "created_by_username",
            "created_at",
            "updated_at",
            "tracks",
        ]
        read_only_fields = ["id", "created_by_username", "created_at", "updated_at"]
