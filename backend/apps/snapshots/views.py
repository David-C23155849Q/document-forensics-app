from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.submissions.models import Submission
from .models import DocumentSnapshot
from .serializers import DocumentSnapshotListSerializer, DocumentSnapshotSerializer


def _check_access(user, submission):
    if user.role == "STUDENT" and submission.student_id != user.id:
        raise PermissionDenied("Not your submission.")
    if user.role == "LECTURER" and submission.assignment.lecturer_id != user.id:
        raise PermissionDenied("Not your assignment.")


class SubmissionSnapshotListView(generics.ListAPIView):
    """GET /submissions/{id}/snapshots/ - paginated, lightweight by default."""

    serializer_class = DocumentSnapshotListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_full_snapshot", "content_changed"]

    def get_queryset(self):
        submission = generics.get_object_or_404(Submission, id=self.kwargs["submission_id"])
        _check_access(self.request.user, submission)
        return DocumentSnapshot.objects.filter(submission=submission).order_by("sequence_number")


class SnapshotDetailView(generics.RetrieveAPIView):
    """GET /submissions/{id}/snapshots/{snapshot_id}/ - full detail incl. content."""

    serializer_class = DocumentSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "snapshot_id"

    def get_queryset(self):
        submission = generics.get_object_or_404(Submission, id=self.kwargs["submission_id"])
        _check_access(self.request.user, submission)
        return DocumentSnapshot.objects.filter(submission=submission)
