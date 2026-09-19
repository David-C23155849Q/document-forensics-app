"""
ReportService: assembles the structured forensic report described in
section 49/90 of the spec. This is deliberately just descriptive evidence
plus the mandatory disclaimer - it never renders a verdict.
"""
from apps.events.models import ForensicEvent
from apps.forensic.services.analytics_service import AnalyticsService
from apps.forensic.services.timeline_service import TimelineService
from apps.ml_analysis.models import MLAnalysis
from apps.sessions.models import WritingSession

DISCLAIMER = (
    "These indicators describe observed document activity and system-generated "
    "anomalies. They are not, by themselves, proof of academic misconduct."
)


class ReportService:
    def __init__(self, submission):
        self.submission = submission

    def build(self) -> dict:
        analytics = AnalyticsService(self.submission).full_analytics()
        timeline = TimelineService(self.submission).build()
        latest_ml = MLAnalysis.objects.filter(submission=self.submission).order_by("-created_at").first()
        large_insertions = ForensicEvent.objects.filter(
            submission=self.submission, event_type=ForensicEvent.EventType.LARGE_INSERTION
        )
        large_deletions = ForensicEvent.objects.filter(
            submission=self.submission, event_type=ForensicEvent.EventType.LARGE_DELETION
        )
        replacements = ForensicEvent.objects.filter(
            submission=self.submission, event_type=ForensicEvent.EventType.REPLACEMENT
        )

        return {
            "student": {
                "id": self.submission.student_id,
                "name": self.submission.student.get_full_name() or self.submission.student.username,
            },
            "assignment": {
                "id": self.submission.assignment_id,
                "title": self.submission.assignment.title,
                "course": self.submission.assignment.course,
            },
            "submission": {
                "id": self.submission.id,
                "status": self.submission.status,
                "started_at": self.submission.started_at,
                "submitted_at": self.submission.submitted_at,
                "final_word_count": self.submission.final_word_count,
            },
            "sessions": WritingSession.objects.filter(submission=self.submission).count(),
            "activity_summary": analytics["sessions"],
            "event_summary": analytics["events"],
            "large_insertions": large_insertions.count(),
            "large_deletions": large_deletions.count(),
            "replacement_events": replacements.count(),
            "timeline": timeline,
            "word_count_trajectory": analytics["word_count_trajectory"],
            "ml_indicators": {
                "anomaly_score": latest_ml.anomaly_score if latest_ml else None,
                "signals": latest_ml.signals if latest_ml else [],
                "model_version": latest_ml.model_version if latest_ml else None,
            } if latest_ml else None,
            "methodology": (
                "Document activity is captured through Office.js at the configured "
                "snapshot interval. Event classifications (e.g. 'large insertion') are "
                "derived by comparing consecutive document states, not by observing "
                "OS-level input directly."
            ),
            "limitations": (
                "Office.js cannot observe clipboard contents, other applications, or "
                "keystrokes outside Word. 'Large insertion' describes a measured change "
                "in document content, not a confirmed paste action, unless Word's API "
                "explicitly reports a paste operation."
            ),
            "disclaimer": DISCLAIMER,
        }
