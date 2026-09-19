"""
TimelineService: groups raw events/sessions into a lecturer-friendly
timeline structure so the frontend never has to render thousands of raw
snapshot rows directly (section 27).
"""
from collections import defaultdict

from apps.events.models import ForensicEvent
from apps.sessions.models import WritingSession


class TimelineService:
    def __init__(self, submission):
        self.submission = submission

    def build(self):
        sessions = WritingSession.objects.filter(submission=self.submission).order_by("started_at")
        events = ForensicEvent.objects.filter(submission=self.submission).order_by("timestamp")

        events_by_session = defaultdict(list)
        for event in events:
            events_by_session[event.session_id].append(event)

        by_date = defaultdict(list)
        for session in sessions:
            date_key = session.started_at.date().isoformat()
            session_events = events_by_session.get(session.id, [])
            by_date[date_key].append({
                "session_id": session.id,
                "start": session.started_at.isoformat(),
                "end": session.ended_at.isoformat() if session.ended_at else None,
                "active_seconds": session.active_seconds,
                "idle_seconds": session.idle_seconds,
                "events": [
                    {
                        "id": e.id,
                        "type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "words_affected": e.words_affected,
                        "characters_affected": e.characters_affected,
                        "confidence": e.classification_confidence,
                    }
                    for e in session_events
                ],
            })

        return [{"date": date, "sessions": sessions_list} for date, sessions_list in sorted(by_date.items())]
