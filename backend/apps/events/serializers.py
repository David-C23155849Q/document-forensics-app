from rest_framework import serializers

from .models import ForensicEvent


class ForensicEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForensicEvent
        fields = [
            "id", "client_event_id", "submission", "session", "event_type", "timestamp",
            "document_position", "paragraph_index", "character_offset",
            "characters_affected", "words_affected", "inserted_text", "deleted_text",
            "previous_word_count", "new_word_count", "snapshot_before", "snapshot_after",
            "detection_method", "classification_confidence", "metadata", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
