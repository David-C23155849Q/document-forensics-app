from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.submissions.models import Submission
from .models import ForensicEvent
from .serializers import ForensicEventSerializer


def _check_access(user, submission):
    if user.role == "STUDENT" and submission.student_id != user.id:
        raise PermissionDenied("Not your submission.")
    if user.role == "LECTURER" and submission.assignment.lecturer_id != user.id:
        raise PermissionDenied("Not your assignment.")


class SubmissionEventListView(generics.ListAPIView):
    """GET /submissions/{id}/events/?event_type=large_insertion&start_time=...&end_time=..."""

    serializer_class = ForensicEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["event_type", "session"]

    def get_queryset(self):
        submission = generics.get_object_or_404(Submission, id=self.kwargs["submission_id"])
        _check_access(self.request.user, submission)
        qs = ForensicEvent.objects.filter(submission=submission).order_by("timestamp")
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")
        if start_time:
            qs = qs.filter(timestamp__gte=start_time)
        if end_time:
            qs = qs.filter(timestamp__lte=end_time)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(inserted_text__icontains=search)
        return qs
