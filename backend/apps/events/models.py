from django.db import models

from apps.sessions.models import WritingSession
from apps.snapshots.models import DocumentSnapshot
from apps.submissions.models import Submission


class ForensicEvent(models.Model):
    class EventType(models.TextChoices):
        SESSION_STARTED = "session_started", "Session started"
        SESSION_ENDED = "session_ended", "Session ended"
        DOCUMENT_OPENED = "document_opened", "Document opened"
        DOCUMENT_CLOSED = "document_closed", "Document closed"
        INSERTION = "insertion", "Insertion"
        DELETION = "deletion", "Deletion"
        REPLACEMENT = "replacement", "Replacement"
        LARGE_INSERTION = "large_insertion", "Large insertion"
        LARGE_DELETION = "large_deletion", "Large deletion"
        FORMATTING_CHANGE = "formatting_change", "Formatting change"
        PARAGRAPH_ADDED = "paragraph_added", "Paragraph added"
        PARAGRAPH_DELETED = "paragraph_deleted", "Paragraph deleted"
        UNDO = "undo", "Undo"
        REDO = "redo", "Redo"
        IDLE_STARTED = "idle_started", "Inactivity period started"
        IDLE_ENDED = "idle_ended", "Inactivity period ended"
        SIGNIFICANT_CHANGE = "significant_change", "Significant change"
        SUBMISSION_STARTED = "submission_started", "Submission started"
        SUBMISSION_COMPLETED = "submission_completed", "Submission completed"
        SYNCHRONIZATION = "synchronization", "Synchronization"
        CONNECTION_LOST = "connection_lost", "Connection lost"
        CONNECTION_RESTORED = "connection_restored", "Connection restored"

    client_event_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="events")
    session = models.ForeignKey(WritingSession, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    timestamp = models.DateTimeField()
    document_position = models.IntegerField(null=True, blank=True)
    paragraph_index = models.IntegerField(null=True, blank=True)
    character_offset = models.IntegerField(null=True, blank=True)
    characters_affected = models.IntegerField(default=0)
    words_affected = models.IntegerField(default=0)
    inserted_text = models.TextField(null=True, blank=True)
    deleted_text = models.TextField(null=True, blank=True)
    previous_word_count = models.IntegerField(default=0)
    new_word_count = models.IntegerField(default=0)
    snapshot_before = models.ForeignKey(
        DocumentSnapshot, on_delete=models.SET_NULL, null=True, blank=True, related_name="events_before"
    )
    snapshot_after = models.ForeignKey(
        DocumentSnapshot, on_delete=models.SET_NULL, null=True, blank=True, related_name="events_after"
    )
    detection_method = models.CharField(max_length=100, blank=True)
    # "classification_confidence" = confidence in the EVENT TYPE label
    # (e.g. "large insertion"), never a probability of misconduct.
    classification_confidence = models.CharField(
        max_length=20,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")],
        default="MEDIUM",
    )
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "timestamp"]),
            models.Index(fields=["submission", "event_type"]),
        ]
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.event_type} @ {self.timestamp}"
