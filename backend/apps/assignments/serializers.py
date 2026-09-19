from rest_framework import serializers

from .models import Assignment


class AssignmentSerializer(serializers.ModelSerializer):
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id", "title", "assignment_code", "course", "description", "instructions",
            "lecturer", "start_time", "deadline", "min_words", "max_words",
            "allowed_file_type", "status", "created_at", "updated_at", "submission_count",
        ]
        read_only_fields = ["id", "lecturer", "created_at", "updated_at"]

    def get_submission_count(self, obj):
        return obj.submissions.count()
