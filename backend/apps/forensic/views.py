from django.conf import settings
from django.utils.dateparse import parse_datetime
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import ForensicEvent
from apps.sessions.models import WritingSession
from apps.snapshots.services import SnapshotManager
from apps.submissions.models import Submission

from .services.analytics_service import AnalyticsService
from .services.document_reconstruction import DocumentReconstructionService
from .services.event_detector import ForensicEventDetector
from .services.timeline_service import TimelineService


def _check_access(user, submission):
    if user.role == "STUDENT" and submission.student_id != user.id:
        raise PermissionDenied("Not your submission.")
    if user.role == "LECTURER" and submission.assignment.lecturer_id != user.id:
        raise PermissionDenied("Not your assignment.")


class SyncView(APIView):
    """
    POST /api/v1/sync/
    Batched, idempotent ingestion of events + snapshots from the add-in's
    offline queue. Duplicate client IDs are safely ignored (section 59).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        submission_id = request.data.get("submission_id")
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Submission not found."}, status=404)
        if request.user.role == "STUDENT" and submission.student_id != request.user.id:
            raise PermissionDenied("Not your submission.")

        max_batch = settings.FORENSIC_CONFIG["MAX_BATCH_SIZE"]
        incoming_events = request.data.get("events", [])[:max_batch]
        incoming_snapshots = request.data.get("snapshots", [])[:max_batch]

        accepted_snapshots, duplicate_snapshots, errors = [], [], []
        snapshot_cache = {}

        for snap_payload in incoming_snapshots:
            try:
                session = WritingSession.objects.get(id=snap_payload["session_id"])
                manager = SnapshotManager(submission, session)
                snapshot = manager.ingest(snap_payload)
                snapshot_cache[snapshot.sequence_number] = snapshot
                accepted_snapshots.append(snapshot.id)
            except Exception as exc:  # noqa: BLE001
                errors.append({"snapshot": snap_payload.get("client_snapshot_id"), "error": str(exc)})

        # Run event detection between consecutive full snapshots that were just ingested.
        full_snapshots = sorted(
            [s for s in snapshot_cache.values() if s.is_full_snapshot], key=lambda s: s.sequence_number
        )
        detected_event_ids = []
        for i in range(1, len(full_snapshots)):
            detector = ForensicEventDetector(submission, full_snapshots[i].session)
            new_events = detector.detect_from_snapshots(full_snapshots[i - 1], full_snapshots[i])
            detected_event_ids.extend(e.id for e in new_events)

        accepted_events, duplicate_events = [], []
        for event_payload in incoming_events:
            client_id = event_payload.get("client_event_id")
            if client_id and ForensicEvent.objects.filter(client_event_id=client_id).exists():
                duplicate_events.append(client_id)
                continue
            try:
                event = ForensicEvent.objects.create(
                    client_event_id=client_id,
                    submission=submission,
                    session_id=event_payload.get("session_id"),
                    event_type=event_payload["event_type"],
                    timestamp=parse_datetime(event_payload["timestamp"]),
                    characters_affected=event_payload.get("characters_affected", 0),
                    words_affected=event_payload.get("words_affected", 0),
                    previous_word_count=event_payload.get("previous_word_count", 0),
                    new_word_count=event_payload.get("new_word_count", 0),
                    detection_method=event_payload.get("detection_method", "client_reported"),
                    classification_confidence=event_payload.get("classification_confidence", "MEDIUM"),
                    metadata=event_payload.get("metadata"),
                )
                accepted_events.append(event.id)
            except Exception as exc:  # noqa: BLE001
                errors.append({"event": client_id, "error": str(exc)})

        from django.utils import timezone
        submission.last_synced_at = timezone.now()
        submission.save(update_fields=["last_synced_at"])

        return Response({
            "accepted_events": accepted_events + detected_event_ids,
            "accepted_snapshots": accepted_snapshots,
            "duplicates": duplicate_events,
            "errors": errors,
        })


class TimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)
        return Response(TimelineService(submission).build())


class DocumentStateView(APIView):
    """GET /submissions/{id}/document/state/?timestamp=..."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)
        timestamp = request.query_params.get("timestamp")
        service = DocumentReconstructionService(submission)
        if timestamp:
            state = service.get_document_at_timestamp(parse_datetime(timestamp))
        else:
            # default: latest state
            from django.utils import timezone
            state = service.get_document_at_timestamp(timezone.now())
        return Response(state)


class CompareView(APIView):
    """GET /submissions/{id}/compare/?before=snapshot_id&after=snapshot_id"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)
        before_id = request.query_params.get("before")
        after_id = request.query_params.get("after")
        service = DocumentReconstructionService(submission)
        return Response(service.compare_snapshots(before_id, after_id))


class ReplayView(APIView):
    """GET /submissions/{id}/replay/?start=...&end=...&step=30"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)
        start = parse_datetime(request.query_params.get("start")) if request.query_params.get("start") else submission.started_at
        end = parse_datetime(request.query_params.get("end")) if request.query_params.get("end") else submission.submitted_at
        step = int(request.query_params.get("step", 30))
        if not start or not end:
            return Response({"detail": "No writing activity recorded yet."}, status=400)
        service = DocumentReconstructionService(submission)
        return Response(service.generate_replay_sequence(start, end, step))


class AnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)
        return Response(AnalyticsService(submission).full_analytics())
