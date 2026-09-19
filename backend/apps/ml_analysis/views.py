from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from apps.submissions.models import Submission
from .models import MLAnalysis
from .serializers import MLAnalysisSerializer


class MLAnalysisView(generics.ListAPIView):
    serializer_class = MLAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        submission = generics.get_object_or_404(Submission, id=self.kwargs["submission_id"])
        user = self.request.user
        if user.role == "STUDENT":
            raise PermissionDenied("Students cannot view forensic ML analysis.")
        if user.role == "LECTURER" and submission.assignment.lecturer_id != user.id:
            raise PermissionDenied("Not your assignment.")
        return MLAnalysis.objects.filter(submission=submission).order_by("-created_at")
