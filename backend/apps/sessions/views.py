from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.submissions.models import Submission
from .models import WritingSession
from .serializers import WritingSessionSerializer


def _assert_owns_submission(user, submission):
    if user.role == "STUDENT" and submission.student_id != user.id:
        raise PermissionDenied("Not your submission.")


class SessionStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        submission_id = request.data.get("submission_id")
        submission = generics.get_object_or_404(Submission, id=submission_id)
        _assert_owns_submission(request.user, submission)
        session = WritingSession.objects.create(
            submission=submission,
            started_at=timezone.now(),
            last_activity=timezone.now(),
            device_info=request.data.get("device_info", ""),
            word_document_id=request.data.get("word_document_id", ""),
        )
        return Response(WritingSessionSerializer(session).data, status=201)


class SessionEndView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = generics.get_object_or_404(WritingSession, id=pk)
        _assert_owns_submission(request.user, session.submission)
        session.ended_at = timezone.now()
        session.active_seconds = request.data.get("active_seconds", session.active_seconds)
        session.idle_seconds = request.data.get("idle_seconds", session.idle_seconds)
        session.save(update_fields=["ended_at", "active_seconds", "idle_seconds"])
        return Response(WritingSessionSerializer(session).data)
