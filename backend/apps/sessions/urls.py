from django.urls import path

from .views import SessionStartView, SessionEndView

urlpatterns = [
    path("sessions/start/", SessionStartView.as_view(), name="session-start"),
    path("sessions/<int:pk>/end/", SessionEndView.as_view(), name="session-end"),
]
