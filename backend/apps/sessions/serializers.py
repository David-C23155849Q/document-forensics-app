from rest_framework import serializers

from .models import WritingSession


class WritingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingSession
        fields = [
            "id", "submission", "started_at", "ended_at", "active_seconds",
            "idle_seconds", "last_activity", "device_info", "word_document_id", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
