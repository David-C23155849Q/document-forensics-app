"""
Core forensic-engine tests. Run with: python manage.py test apps.forensic
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.assignments.models import Assignment
from apps.events.models import ForensicEvent
from apps.sessions.models import WritingSession
from apps.snapshots.models import DocumentSnapshot
from apps.submissions.models import Submission

from ..services.diff_engine import DiffEngine
from ..services.document_reconstruction import DocumentReconstructionService
from ..services.event_detector import ForensicEventDetector

User = get_user_model()


class DiffEngineTests(TestCase):
    def test_detects_insertion(self):
        diffs = DiffEngine.diff_words("the cat sat", "the cat sat on the mat")
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0].op, "insert")
        self.assertEqual(diffs[0].new_words, ["on", "the", "mat"])

    def test_apply_diff_round_trip(self):
        old = "the cat sat"
        new = "the cat sat on the mat"
        diffs = DiffEngine.diff_words(old, new)
        serialized = DiffEngine.serialize(diffs)
        reconstructed = DiffEngine.apply_diff(old, serialized)
        self.assertEqual(reconstructed, new)


class ForensicEventDetectorTests(TestCase):
    def setUp(self):
        lecturer = User.objects.create_user(username="lect", password="x", role="LECTURER")
        student = User.objects.create_user(username="stud", password="x", role="STUDENT")
        assignment = Assignment.objects.create(
            title="Test", assignment_code="T1", course="CS", lecturer=lecturer,
            start_time=timezone.now(), deadline=timezone.now(),
        )
        self.submission = Submission.objects.create(assignment=assignment, student=student)
        self.session = WritingSession.objects.create(submission=self.submission, started_at=timezone.now())

    def _snapshot(self, text, seq):
        return DocumentSnapshot.objects.create(
            submission=self.submission, session=self.session, timestamp=timezone.now(),
            sequence_number=seq, word_count=len(text.split()), character_count=len(text),
            full_content=text, is_full_snapshot=True, content_changed=True,
        )

    def test_large_insertion_is_flagged_not_accused(self):
        old_text = "The database stores information."
        new_text = old_text + " " + " ".join(["extra"] * 150)
        prev = self._snapshot(old_text, 1)
        curr = self._snapshot(new_text, 2)

        detector = ForensicEventDetector(self.submission, self.session)
        events = detector.detect_from_snapshots(prev, curr)

        self.assertTrue(any(e.event_type == ForensicEvent.EventType.LARGE_INSERTION for e in events))
        for e in events:
            # Guard against the spec's "no automatic accusation" requirement.
            self.assertNotIn("cheat", (e.metadata or {}).get("note", "").lower())


class DocumentReconstructionTests(TestCase):
    def setUp(self):
        lecturer = User.objects.create_user(username="lect2", password="x", role="LECTURER")
        student = User.objects.create_user(username="stud2", password="x", role="STUDENT")
        assignment = Assignment.objects.create(
            title="Test2", assignment_code="T2", course="CS", lecturer=lecturer,
            start_time=timezone.now(), deadline=timezone.now(),
        )
        self.submission = Submission.objects.create(assignment=assignment, student=student)
        self.session = WritingSession.objects.create(submission=self.submission, started_at=timezone.now())

    def test_reconstructs_latest_full_snapshot(self):
        t1 = timezone.now()
        DocumentSnapshot.objects.create(
            submission=self.submission, session=self.session, timestamp=t1, sequence_number=1,
            word_count=2, character_count=10, full_content="hello world", is_full_snapshot=True,
        )
        service = DocumentReconstructionService(self.submission)
        state = service.get_document_at_timestamp(t1)
        self.assertEqual(state["content"], "hello world")
