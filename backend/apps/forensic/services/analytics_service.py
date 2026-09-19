from apps.events.models import ForensicEvent
from apps.sessions.models import WritingSession
from apps.snapshots.models import DocumentSnapshot


class AnalyticsService:
    def __init__(self, submission):
        self.submission = submission

    def word_count_trajectory(self):
        snapshots = (
            DocumentSnapshot.objects.filter(submission=self.submission, content_changed=True)
            .order_by("timestamp")
            .values("timestamp", "word_count")
        )
        return [{"timestamp": s["timestamp"].isoformat(), "word_count": s["word_count"]} for s in snapshots]

    def session_summary(self):
        sessions = WritingSession.objects.filter(submission=self.submission)
        return {
            "session_count": sessions.count(),
            "total_active_seconds": sum(s.active_seconds for s in sessions),
            "total_idle_seconds": sum(s.idle_seconds for s in sessions),
        }

    def event_summary(self):
        events = ForensicEvent.objects.filter(submission=self.submission)
        counts = {}
        for choice, _ in ForensicEvent.EventType.choices:
            counts[choice] = events.filter(event_type=choice).count()
        large_insertions = events.filter(event_type=ForensicEvent.EventType.LARGE_INSERTION)
        max_insertion = max((e.words_affected for e in large_insertions), default=0)
        idle_events = events.filter(event_type=ForensicEvent.EventType.IDLE_STARTED)
        longest_idle = max((e.metadata or {}).get("gap_seconds", 0) for e in idle_events) if idle_events else 0
        return {
            "counts_by_type": counts,
            "total_events": events.count(),
            "max_insertion_words": max_insertion,
            "longest_inactivity_seconds": longest_idle,
        }

    def full_analytics(self):
        return {
            "word_count_trajectory": self.word_count_trajectory(),
            "sessions": self.session_summary(),
            "events": self.event_summary(),
        }
