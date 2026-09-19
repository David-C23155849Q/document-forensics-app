from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.assignments.models import Assignment
from apps.audit.services import log_action
from .models import Submission
from .serializers import SubmissionSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    filterset_fields = ["status", "assignment"]
    http_method_names = ["get", "post", "head"]

    def get_queryset(self):
        user = self.request.user
        qs = Submission.objects.select_related("assignment", "student")
        if user.role == "STUDENT":
            # Ownership enforcement: students can only ever see their own rows,
            # regardless of what ID is requested in the URL (prevents IDOR).
            return qs.filter(student=user)
        if user.role == "LECTURER":
            return qs.filter(assignment__lecturer=user)
        return qs

    def create(self, request, *args, **kwargs):
        """Student starts an assignment -> creates/returns a Submission."""
        assignment_id = request.data.get("assignment")
        assignment = Assignment.objects.filter(id=assignment_id).first()
        if not assignment:
            return Response({"detail": "Assignment not found."}, status=404)
        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={"status": Submission.Status.IN_PROGRESS, "started_at": timezone.now()},
        )
        if created:
            log_action(request.user, "submission.started", submission, request)
        return Response(SubmissionSerializer(submission).data, status=201 if created else 200)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        submission = self.get_object()
        if submission.student_id != request.user.id:
            raise PermissionDenied("You may only submit your own assignment.")
        submission.status = Submission.Status.SUBMITTED
        submission.submitted_at = timezone.now()
        submission.save(update_fields=["status", "submitted_at"])
        log_action(request.user, "submission.submitted", submission, request)
        return Response(SubmissionSerializer(submission).data)
