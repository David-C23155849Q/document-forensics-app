from django.urls import path

from .views import MLAnalysisView

urlpatterns = [
    path("submissions/<int:submission_id>/ml-analysis/", MLAnalysisView.as_view(), name="submission-ml-analysis"),
]
