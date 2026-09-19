from rest_framework.permissions import BasePermission


class IsLecturer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == "LECTURER")


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == "STUDENT")


class IsOwnerOrLecturer(BasePermission):
    """
    Object-level check: a student may only access their own submission-linked
    objects; a lecturer may access submissions for assignments they own.
    This is the safeguard against IDOR (section 52: a student must never be
    able to fetch another student's submission by guessing an ID).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        submission = getattr(obj, "submission", obj)
        if user.role == "STUDENT":
            return submission.student_id == user.id
        if user.role == "LECTURER":
            return submission.assignment.lecturer_id == user.id
        return user.role == "ADMIN"
