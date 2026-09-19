from rest_framework import generics, permissions

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["action", "user"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return AuditLog.objects.all()
        if user.role == "LECTURER":
            return AuditLog.objects.filter(user=user)
        return AuditLog.objects.none()
