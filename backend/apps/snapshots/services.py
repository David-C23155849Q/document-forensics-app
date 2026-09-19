"""
SnapshotManager: responsible for deciding whether an incoming snapshot is a
heartbeat (no content change) or requires a full checkpoint, and for
computing hashes so identical content is never stored twice.
"""
import hashlib

from django.conf import settings
from django.utils.dateparse import parse_datetime

from .models import DocumentSnapshot


def hash_content(content: str) -> str:
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


class SnapshotManager:
    def __init__(self, submission, session):
        self.submission = submission
        self.session = session

    def _last_full_snapshot(self):
        return (
            DocumentSnapshot.objects.filter(submission=self.submission, is_full_snapshot=True)
            .order_by("-sequence_number")
            .first()
        )

    def should_take_full_snapshot(self, timestamp, force=False) -> bool:
        if force:
            return True
        last_full = self._last_full_snapshot()
        if last_full is None:
            return True
        interval = settings.FORENSIC_CONFIG["FULL_SNAPSHOT_INTERVAL_SECONDS"]
        elapsed = (timestamp - last_full.timestamp).total_seconds()
        return elapsed >= interval

    def ingest(self, payload: dict) -> DocumentSnapshot:
        """
        payload keys: client_snapshot_id, timestamp (iso str), sequence_number,
        word_count, character_count, paragraph_count, cursor_position,
        content, content_changed, change_type, diff, force_full
        """
        client_id = payload.get("client_snapshot_id")
        if client_id:
            existing = DocumentSnapshot.objects.filter(client_snapshot_id=client_id).first()
            if existing:
                return existing  # idempotent: duplicate upload, ignore silently

        timestamp = payload["timestamp"]
        if isinstance(timestamp, str):
            timestamp = parse_datetime(timestamp)

        content = payload.get("content")
        content_hash = hash_content(content) if content is not None else ""
        is_full = self.should_take_full_snapshot(timestamp, force=payload.get("force_full", False))

        last_snapshot = (
            DocumentSnapshot.objects.filter(submission=self.submission)
            .order_by("-sequence_number")
            .first()
        )

        # Avoid storing an identical full document twice in a row.
        if is_full and last_snapshot and last_snapshot.content_hash == content_hash and content_hash:
            is_full = False

        snapshot = DocumentSnapshot.objects.create(
            client_snapshot_id=client_id,
            submission=self.submission,
            session=self.session,
            timestamp=timestamp,
            sequence_number=payload["sequence_number"],
            document_version=payload.get("document_version", 1),
            word_count=payload.get("word_count", 0),
            character_count=payload.get("character_count", 0),
            paragraph_count=payload.get("paragraph_count", 0),
            cursor_position=payload.get("cursor_position"),
            content_hash=content_hash,
            content_changed=payload.get("content_changed", False),
            change_type=payload.get("change_type", ""),
            diff=payload.get("diff"),
            full_content=content if is_full else None,
            is_full_snapshot=is_full,
            previous_snapshot=last_snapshot,
        )
        return snapshot
