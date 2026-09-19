"""
Lightweight middleware that records lecturer access to sensitive forensic
views (viewing a submission, replay, report export). Deliberately narrow:
it only logs a specific allow-list of paths rather than every request, to
avoid bloating the audit log with routine traffic.
"""
import re

SENSITIVE_PATH_PATTERNS = [
    re.compile(r"^/api/v1/submissions/\d+/(timeline|document|replay|analytics|compare)"),
    re.compile(r"^/api/v1/submissions/\d+/report"),
]


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False) and getattr(user, "role", None) == "LECTURER":
            for pattern in SENSITIVE_PATH_PATTERNS:
                if pattern.match(request.path):
                    from .services import log_action
                    log_action(user, f"view:{request.path}", request=request)
                    break
        return response
