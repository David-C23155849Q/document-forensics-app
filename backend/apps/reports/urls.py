from django.urls import path

from .views import ReportView

urlpatterns = [
    path("submissions/<int:submission_id>/report/", ReportView.as_view(), name="submission-report"),
]
