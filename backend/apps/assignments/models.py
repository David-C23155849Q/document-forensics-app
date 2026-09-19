from django.conf import settings
from django.db import models


class Assignment(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SCHEDULED = "SCHEDULED", "Scheduled"
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    title = models.CharField(max_length=255)
    assignment_code = models.CharField(max_length=50, unique=True)
    course = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments"
    )
    start_time = models.DateTimeField()
    deadline = models.DateTimeField()
    min_words = models.PositiveIntegerField(default=0)
    max_words = models.PositiveIntegerField(default=0)
    allowed_file_type = models.CharField(max_length=50, default="docx")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["lecturer", "status"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.assignment_code})"
