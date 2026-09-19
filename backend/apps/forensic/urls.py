from django.urls import path

from .views import (
    AnalyticsView,
    CompareView,
    DocumentStateView,
    ReplayView,
    SyncView,
    TimelineView,
)

urlpatterns = [
    path("sync/", SyncView.as_view(), name="sync"),
    path("submissions/<int:submission_id>/timeline/", TimelineView.as_view(), name="submission-timeline"),
    path("submissions/<int:submission_id>/document/state/", DocumentStateView.as_view(), name="submission-document-state"),
    path("submissions/<int:submission_id>/compare/", CompareView.as_view(), name="submission-compare"),
    path("submissions/<int:submission_id>/replay/", ReplayView.as_view(), name="submission-replay"),
    path("submissions/<int:submission_id>/analytics/", AnalyticsView.as_view(), name="submission-analytics"),
]
