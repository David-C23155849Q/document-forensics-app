import csv

from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import log_action
from apps.events.models import ForensicEvent
from apps.submissions.models import Submission

from .services import ReportService


def _check_access(user, submission):
    if user.role == "STUDENT" and submission.student_id != user.id:
        raise PermissionDenied("Not your submission.")
    if user.role == "LECTURER" and submission.assignment.lecturer_id != user.id:
        raise PermissionDenied("Not your assignment.")


class ReportView(APIView):
    """
    GET /submissions/{id}/report/?format=json|csv
    PDF export is intentionally not implemented in this build (would
    require a PDF rendering pipeline / wkhtmltopdf-equivalent); JSON and
    CSV are fully functional and a PDF template can be layered on top of
    ReportService.build() later without changing the underlying data.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        submission = Submission.objects.filter(id=submission_id).first()
        if not submission:
            return Response({"detail": "Not found."}, status=404)
        _check_access(request.user, submission)

        fmt = request.query_params.get("format", "json")
        report = ReportService(submission).build()
        log_action(request.user, "report.exported", submission, request, metadata={"format": fmt})

        if fmt == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="submission_{submission.id}_events.csv"'
            writer = csv.writer(response)
            writer.writerow(["timestamp", "event_type", "words_affected", "characters_affected", "confidence"])
            for event in ForensicEvent.objects.filter(submission=submission).order_by("timestamp"):
                writer.writerow([event.timestamp, event.event_type, event.words_affected,
                                  event.characters_affected, event.classification_confidence])
            return response

        return Response(report)
