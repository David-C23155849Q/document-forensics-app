from django.utils import timezone
from rest_framework import viewsets, permissions

from apps.accounts.permissions import IsLecturer
from .models import Assignment
from .serializers import AssignmentSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    filterset_fields = ["status", "course"]

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), IsLecturer()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.all()
        if user.role == "LECTURER":
            return qs.filter(lecturer=user)
        if user.role == "STUDENT":
            # Students only ever see assignments that are visible/active,
            # never another lecturer's drafts.
            return qs.exclude(status=Assignment.Status.DRAFT).filter(
                start_time__lte=timezone.now()
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(lecturer=self.request.user)
