from django.db import models

from apps.submissions.models import Submission


class MLAnalysis(models.Model):
    """
    Stores descriptive, non-accusatory ML output. `anomaly_score` and the
    other scores are NOT probabilities of academic misconduct - they
    describe how unusual an aspect of the writing activity is relative to
    the submission's own baseline. See docs/forensic-methodology.md.
    """

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="ml_analyses")
    model_version = models.CharField(max_length=50, default="isolation-forest-v1")
    anomaly_score = models.FloatField(default=0.0)
    writing_pattern_score = models.FloatField(default=0.0)
    insertion_pattern_score = models.FloatField(default=0.0)
    editing_pattern_score = models.FloatField(default=0.0)
    authorship_consistency_indicator = models.FloatField(null=True, blank=True)
    analysis_summary = models.TextField(blank=True)
    feature_data = models.JSONField(null=True, blank=True)
    signals = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"MLAnalysis for submission {self.submission_id} (score={self.anomaly_score:.2f})"
