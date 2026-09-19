from rest_framework import serializers

from .models import DocumentSnapshot


class DocumentSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSnapshot
        fields = [
            "id", "client_snapshot_id", "submission", "session", "timestamp", "sequence_number",
            "document_version", "word_count", "character_count", "paragraph_count",
            "cursor_position", "content_hash", "content_changed", "change_type", "diff",
            "full_content", "is_full_snapshot", "previous_snapshot", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DocumentSnapshotListSerializer(serializers.ModelSerializer):
    """Lightweight version for large listings - excludes full_content."""

    class Meta:
        model = DocumentSnapshot
        fields = [
            "id", "timestamp", "sequence_number", "word_count", "character_count",
            "content_changed", "change_type", "is_full_snapshot",
        ]
