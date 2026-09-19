"""
ForensicEventDetector: compares consecutive document states and produces
ForensicEvent records. Detection logic lives here, kept out of API views
per the spec's architectural requirement (section 61/66).

IMPORTANT: this module only ever produces descriptive, evidence-based
event types (e.g. "large_insertion"). It never labels anything as
academic misconduct - that judgment is left entirely to the lecturer.
"""
from django.conf import settings
from django.utils import timezone

from apps.events.models import ForensicEvent
from .diff_engine import DiffEngine


class ForensicEventDetector:
    def __init__(self, submission, session):
        self.submission = submission
        self.session = session
        self.config = settings.FORENSIC_CONFIG

    def _classify_insertion_size(self, word_delta: int) -> str:
        large = self.config["LARGE_INSERTION_WORD_THRESHOLD"]
        medium = self.config["MEDIUM_INSERTION_WORD_THRESHOLD"]
        if word_delta >= large:
            return ForensicEvent.EventType.LARGE_INSERTION
        if word_delta >= medium:
            return ForensicEvent.EventType.INSERTION
        return ForensicEvent.EventType.INSERTION

    def detect_from_snapshots(self, previous_snapshot, current_snapshot):
        """
        Compare two full-content snapshots and emit ForensicEvent rows.
        Returns the list of created events.
        """
        events = []
        if previous_snapshot is None or current_snapshot.full_content is None:
            return events

        old_text = previous_snapshot.full_content or ""
        new_text = current_snapshot.full_content or ""
        if old_text == new_text:
            return events

        diff_ops = DiffEngine.diff_words(old_text, new_text)
        for op in diff_ops:
            inserted_words = len(op.new_words)
            deleted_words = len(op.old_words)

            if op.op == "insert":
                event_type = self._classify_insertion_size(inserted_words)
                confidence = "HIGH" if inserted_words >= self.config["LARGE_INSERTION_WORD_THRESHOLD"] else "MEDIUM"
                events.append(self._create_event(
                    event_type=event_type,
                    previous_snapshot=previous_snapshot,
                    current_snapshot=current_snapshot,
                    words_affected=inserted_words,
                    characters_affected=len(" ".join(op.new_words)),
                    inserted_text=" ".join(op.new_words),
                    character_offset=op.old_start,
                    detection_method="document_state_diff",
                    confidence=confidence,
                ))
            elif op.op == "delete":
                event_type = (
                    ForensicEvent.EventType.LARGE_DELETION
                    if deleted_words >= self.config["LARGE_INSERTION_WORD_THRESHOLD"]
                    else ForensicEvent.EventType.DELETION
                )
                events.append(self._create_event(
                    event_type=event_type,
                    previous_snapshot=previous_snapshot,
                    current_snapshot=current_snapshot,
                    words_affected=deleted_words,
                    characters_affected=len(" ".join(op.old_words)),
                    deleted_text=" ".join(op.old_words),
                    character_offset=op.old_start,
                    detection_method="document_state_diff",
                    confidence="MEDIUM",
                ))
            elif op.op == "replace":
                events.append(self._create_event(
                    event_type=ForensicEvent.EventType.REPLACEMENT,
                    previous_snapshot=previous_snapshot,
                    current_snapshot=current_snapshot,
                    words_affected=max(inserted_words, deleted_words),
                    characters_affected=len(" ".join(op.new_words)),
                    inserted_text=" ".join(op.new_words),
                    deleted_text=" ".join(op.old_words),
                    character_offset=op.old_start,
                    detection_method="document_state_diff",
                    confidence="MEDIUM",
                ))
        return events

    def _create_event(self, event_type, previous_snapshot, current_snapshot, words_affected,
                       characters_affected, character_offset, detection_method, confidence,
                       inserted_text=None, deleted_text=None):
        return ForensicEvent.objects.create(
            submission=self.submission,
            session=self.session,
            event_type=event_type,
            timestamp=current_snapshot.timestamp,
            character_offset=character_offset,
            characters_affected=characters_affected,
            words_affected=words_affected,
            inserted_text=inserted_text,
            deleted_text=deleted_text,
            previous_word_count=previous_snapshot.word_count,
            new_word_count=current_snapshot.word_count,
            snapshot_before=previous_snapshot,
            snapshot_after=current_snapshot,
            detection_method=detection_method,
            classification_confidence=confidence,
            metadata={
                "duration_seconds": max(
                    0, (current_snapshot.timestamp - previous_snapshot.timestamp).total_seconds()
                ),
            },
        )

    def detect_idle(self, last_activity_timestamp, current_timestamp):
        """Returns 'idle_started' event data if the gap exceeds the configured threshold."""
        gap = (current_timestamp - last_activity_timestamp).total_seconds()
        if gap >= self.config["IDLE_THRESHOLD_SECONDS"]:
            return ForensicEvent.objects.create(
                submission=self.submission,
                session=self.session,
                event_type=ForensicEvent.EventType.IDLE_STARTED,
                timestamp=last_activity_timestamp,
                detection_method="inactivity_gap",
                classification_confidence="HIGH",
                metadata={"gap_seconds": gap, "note": "Inactivity period - not evidence of intent."},
            )
        return None
