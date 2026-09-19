from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.assignments.urls")),
    path("api/v1/", include("apps.submissions.urls")),
    path("api/v1/", include("apps.sessions.urls")),
    path("api/v1/", include("apps.snapshots.urls")),
    path("api/v1/", include("apps.events.urls")),
    path("api/v1/", include("apps.forensic.urls")),
    path("api/v1/", include("apps.ml_analysis.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.audit.urls")),
]
