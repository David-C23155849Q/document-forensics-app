from django.db import models

from apps.submissions.models import Submission


class WritingSession(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="writing_sessions")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    word_document_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["submission", "started_at"])]

    def __str__(self):
        return f"Session {self.id} for submission {self.submission_id}"
