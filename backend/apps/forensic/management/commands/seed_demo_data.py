"""
python manage.py seed_demo_data

Creates a lecturer, a few students, one assignment, and a fully realistic
submission history matching the acceptance-criteria scenario in the spec:
normal writing, a 632-word large insertion, continued editing, a 5-minute
idle period, and a final submission - so the whole dashboard can be
exercised end-to-end without manually touching the database.
"""
import hashlib
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import LecturerProfile, StudentProfile, User
from apps.assignments.models import Assignment
from apps.events.models import ForensicEvent
from apps.sessions.models import WritingSession
from apps.snapshots.models import DocumentSnapshot
from apps.submissions.models import Submission

LOREM_SENTENCES = [
    "The database stores information about students and courses.",
    "Relational databases enforce integrity through constraints and keys.",
    "Normalization reduces redundancy across related tables.",
    "Indexes improve query performance at the cost of write overhead.",
    "Transactions guarantee atomicity, consistency, isolation and durability.",
    "A well-designed schema reflects the underlying business domain.",
    "Query optimizers choose execution plans based on statistics.",
    "Backups and replication protect against data loss.",
]

LARGE_INSERTION_TEXT = " ".join(
    [
        "Furthermore, modern database systems increasingly rely on distributed "
        "architectures to achieve horizontal scalability across commodity hardware."
    ]
    * 60
)  # roughly 600+ words


def word_count(text):
    return len(text.split())


class Command(BaseCommand):
    help = "Seed the database with a realistic demo scenario."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        lecturer, _ = User.objects.get_or_create(
            username="lecturer1",
            defaults={"email": "lecturer1@example.edu", "role": User.Role.LECTURER,
                      "first_name": "Alice", "last_name": "Nkomo"},
        )
        lecturer.set_password("password123")
        lecturer.save()
        LecturerProfile.objects.get_or_create(user=lecturer, defaults={"staff_number": "STAFF-001", "department": "Computer Science"})

        students = []
        for i, name in enumerate([("John", "Doe"), ("Jane", "Smith"), ("Kofi", "Mensah")], start=1):
            student, _ = User.objects.get_or_create(
                username=f"student{i}",
                defaults={"email": f"student{i}@example.edu", "role": User.Role.STUDENT,
                          "first_name": name[0], "last_name": name[1]},
            )
            student.set_password("password123")
            student.save()
            StudentProfile.objects.get_or_create(user=student, defaults={"student_number": f"STU-00{i}", "programme": "BSc Computer Science"})
            students.append(student)

        now = timezone.now()
        assignment, _ = Assignment.objects.get_or_create(
            assignment_code="DBS-2026",
            defaults={
                "title": "Database Systems Research Assignment",
                "course": "BSc Computer Science — Database Systems",
                "description": "Write a research report on modern database architectures.",
                "instructions": "Minimum 1500 words. Cover normalization, indexing, and scalability.",
                "lecturer": lecturer,
                "start_time": now - timedelta(days=5),
                "deadline": now + timedelta(days=10),
                "min_words": 1500,
                "max_words": 3000,
                "status": Assignment.Status.ACTIVE,
            },
        )

        # Build the full acceptance-criteria writing history for student 1 (John Doe).
        student = students[0]
        submission, _ = Submission.objects.get_or_create(
            assignment=assignment, student=student,
            defaults={"status": Submission.Status.IN_PROGRESS, "started_at": now - timedelta(hours=3)},
        )

        session_start = now - timedelta(hours=3)
        session = WritingSession.objects.create(
            submission=submission, started_at=session_start, last_activity=session_start,
        )

        text = ""
        seq = 0
        prev_snapshot = None

        def take_snapshot(new_text, ts, change_type="insertion", is_full=True):
            nonlocal seq, prev_snapshot
            seq += 1
            snap = DocumentSnapshot.objects.create(
                submission=submission, session=session, timestamp=ts, sequence_number=seq,
                word_count=word_count(new_text), character_count=len(new_text),
                paragraph_count=new_text.count("\n") + 1, content_hash=hashlib.sha256(new_text.encode()).hexdigest(),
                content_changed=True, change_type=change_type, full_content=new_text,
                is_full_snapshot=is_full, previous_snapshot=prev_snapshot,
            )
            prev_snapshot = snap
            return snap

        t = session_start
        snap0 = take_snapshot("", t, change_type="session_started")
        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.SESSION_STARTED,
            timestamp=t, detection_method="session_lifecycle", classification_confidence="HIGH",
        )

        # Normal writing: a handful of sentences added gradually.
        for i, sentence in enumerate(LOREM_SENTENCES):
            t = t + timedelta(minutes=random.randint(3, 8))
            text = (text + " " + sentence).strip()
            snap = take_snapshot(text, t)
            ForensicEvent.objects.create(
                submission=submission, session=session, event_type=ForensicEvent.EventType.INSERTION,
                timestamp=t, words_affected=word_count(sentence), characters_affected=len(sentence),
                inserted_text=sentence, previous_word_count=word_count(text) - word_count(sentence),
                new_word_count=word_count(text), snapshot_before=prev_snapshot, snapshot_after=snap,
                detection_method="document_state_diff", classification_confidence="MEDIUM",
            )

        # The large insertion (the scenario's key event: 632-ish words in ~1 second).
        t = t + timedelta(minutes=6)
        prev_text = text
        text = text + " " + LARGE_INSERTION_TEXT
        snap_before = prev_snapshot
        snap_after = take_snapshot(text, t, change_type="large_insertion")
        large_event = ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.LARGE_INSERTION,
            timestamp=t, words_affected=word_count(LARGE_INSERTION_TEXT),
            characters_affected=len(LARGE_INSERTION_TEXT), inserted_text=LARGE_INSERTION_TEXT,
            previous_word_count=word_count(prev_text), new_word_count=word_count(text),
            snapshot_before=snap_before, snapshot_after=snap_after,
            detection_method="document_state_diff", classification_confidence="HIGH",
            metadata={"duration_seconds": 1.2, "note": "Large insertion detected; not evidence of copying."},
        )

        # Editing after the insertion.
        t = t + timedelta(minutes=1)
        edit_sentence = "This section requires further citation before submission."
        text = text + " " + edit_sentence
        snap = take_snapshot(text, t)
        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.INSERTION,
            timestamp=t, words_affected=word_count(edit_sentence), characters_affected=len(edit_sentence),
            inserted_text=edit_sentence, previous_word_count=word_count(text) - word_count(edit_sentence),
            new_word_count=word_count(text), snapshot_before=prev_snapshot, snapshot_after=snap,
            detection_method="document_state_diff", classification_confidence="MEDIUM",
        )

        # Idle period.
        idle_start = t + timedelta(minutes=5)
        idle_end = idle_start + timedelta(minutes=5)
        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.IDLE_STARTED,
            timestamp=idle_start, detection_method="inactivity_gap", classification_confidence="HIGH",
            metadata={"gap_seconds": 300, "note": "Inactivity period - not evidence of intent."},
        )
        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.IDLE_ENDED,
            timestamp=idle_end, detection_method="inactivity_gap", classification_confidence="HIGH",
        )

        # Resume writing and finish.
        t = idle_end + timedelta(minutes=2)
        closing = "In conclusion, database architecture choices materially affect scalability and integrity."
        text = text + " " + closing
        snap = take_snapshot(text, t)
        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.INSERTION,
            timestamp=t, words_affected=word_count(closing), characters_affected=len(closing),
            inserted_text=closing, previous_word_count=word_count(text) - word_count(closing),
            new_word_count=word_count(text), snapshot_before=prev_snapshot, snapshot_after=snap,
            detection_method="document_state_diff", classification_confidence="MEDIUM",
        )

        session.ended_at = t + timedelta(minutes=1)
        session.active_seconds = int((session.ended_at - session_start).total_seconds()) - 300
        session.idle_seconds = 300
        session.save()

        submission.status = Submission.Status.SUBMITTED
        submission.submitted_at = session.ended_at
        submission.final_word_count = word_count(text)
        submission.final_character_count = len(text)
        submission.last_synced_at = session.ended_at
        submission.save()

        ForensicEvent.objects.create(
            submission=submission, session=session, event_type=ForensicEvent.EventType.SUBMISSION_COMPLETED,
            timestamp=session.ended_at, detection_method="submission_lifecycle", classification_confidence="HIGH",
        )

        # Lighter, less eventful histories for the other two students.
        for other in students[1:]:
            other_submission, _ = Submission.objects.get_or_create(
                assignment=assignment, student=other,
                defaults={"status": Submission.Status.IN_PROGRESS, "started_at": now - timedelta(hours=1)},
            )
            other_session = WritingSession.objects.create(
                submission=other_submission, started_at=now - timedelta(hours=1), last_activity=now,
            )
            running_text = ""
            for j, sentence in enumerate(random.sample(LOREM_SENTENCES, 4)):
                running_text = (running_text + " " + sentence).strip()
                DocumentSnapshot.objects.create(
                    submission=other_submission, session=other_session, timestamp=now - timedelta(minutes=40 - j * 8),
                    sequence_number=j + 1, word_count=word_count(running_text), character_count=len(running_text),
                    content_hash=hashlib.sha256(running_text.encode()).hexdigest(), content_changed=True,
                    full_content=running_text, is_full_snapshot=True,
                )

        self.stdout.write(self.style.SUCCESS(
            "Demo data created. Login as lecturer1/password123 or student1/password123 (password123 for all)."
        ))
