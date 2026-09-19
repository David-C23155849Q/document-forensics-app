"""
DocumentReconstructionService: rebuilds the document's text at any
requested timestamp by loading the nearest preceding full snapshot and
applying subsequent diffs. Powers the document viewer and replay engine.
"""
from apps.snapshots.models import DocumentSnapshot
from .diff_engine import DiffEngine


class DocumentReconstructionService:
    def __init__(self, submission):
        self.submission = submission

    def _nearest_full_snapshot(self, timestamp):
        return (
            DocumentSnapshot.objects.filter(
                submission=self.submission, is_full_snapshot=True, timestamp__lte=timestamp
            )
            .order_by("-timestamp")
            .first()
        )

    def get_document_at_timestamp(self, timestamp) -> dict:
        checkpoint = self._nearest_full_snapshot(timestamp)
        if checkpoint is None:
            return {"content": "", "word_count": 0, "snapshot_id": None}

        text = checkpoint.full_content or ""
        intermediate = (
            DocumentSnapshot.objects.filter(
                submission=self.submission,
                timestamp__gt=checkpoint.timestamp,
                timestamp__lte=timestamp,
            )
            .order_by("timestamp")
        )
        last_snapshot = checkpoint
        for snap in intermediate:
            if snap.is_full_snapshot and snap.full_content is not None:
                text = snap.full_content
            elif snap.diff:
                text = DiffEngine.apply_diff(text, snap.diff)
            last_snapshot = snap

        return {
            "content": text,
            "word_count": last_snapshot.word_count,
            "character_count": last_snapshot.character_count,
            "snapshot_id": last_snapshot.id,
            "timestamp": last_snapshot.timestamp,
        }

    def get_document_at_snapshot(self, snapshot_id) -> dict:
        snapshot = DocumentSnapshot.objects.get(id=snapshot_id, submission=self.submission)
        return self.get_document_at_timestamp(snapshot.timestamp)

    def compare_snapshots(self, snapshot_id_a, snapshot_id_b) -> dict:
        state_a = self.get_document_at_snapshot(snapshot_id_a)
        state_b = self.get_document_at_snapshot(snapshot_id_b)
        diff_ops = DiffEngine.diff_words(state_a["content"], state_b["content"])
        return {
            "before": state_a,
            "after": state_b,
            "diff": DiffEngine.serialize(diff_ops),
        }

    def generate_replay_sequence(self, start_timestamp, end_timestamp, step_seconds=30):
        """Yields a list of {timestamp, snapshot_id, word_count} checkpoints for scrubbing."""
        from datetime import timedelta

        sequence = []
        cursor = start_timestamp
        while cursor <= end_timestamp:
            state = self.get_document_at_timestamp(cursor)
            sequence.append({
                "timestamp": cursor.isoformat(),
                "snapshot_id": state["snapshot_id"],
                "word_count": state["word_count"],
            })
            cursor += timedelta(seconds=step_seconds)
        return sequence
