from django.db import models

from apps.sessions.models import WritingSession
from apps.submissions.models import Submission


class DocumentSnapshot(models.Model):
    """
    A point-in-time record of document state. `full_content` is populated
    for full snapshots (periodic checkpoints); lightweight heartbeat rows
    leave it null and rely on `diff` + `content_hash` for reconstruction.
    """

    client_snapshot_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="snapshots")
    session = models.ForeignKey(WritingSession, on_delete=models.CASCADE, related_name="snapshots")
    timestamp = models.DateTimeField()
    sequence_number = models.PositiveIntegerField()
    document_version = models.PositiveIntegerField(default=1)
    word_count = models.PositiveIntegerField(default=0)
    character_count = models.PositiveIntegerField(default=0)
    paragraph_count = models.PositiveIntegerField(default=0)
    cursor_position = models.IntegerField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    content_changed = models.BooleanField(default=False)
    change_type = models.CharField(max_length=50, blank=True)
    diff = models.JSONField(null=True, blank=True)
    full_content = models.TextField(null=True, blank=True)
    is_full_snapshot = models.BooleanField(default=False)
    previous_snapshot = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="next_snapshots"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "timestamp"]),
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["submission", "sequence_number"]),
        ]
        ordering = ["sequence_number"]

    def __str__(self):
        return f"Snapshot #{self.sequence_number} ({'full' if self.is_full_snapshot else 'heartbeat'})"
