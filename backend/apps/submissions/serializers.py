from rest_framework import serializers

from .models import Submission


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    assignment_title = serializers.CharField(source="assignment.title", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "assignment", "assignment_title", "student", "student_name", "status",
            "started_at", "submitted_at", "last_synced_at",
            "final_word_count", "final_character_count", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "student", "started_at", "submitted_at", "last_synced_at",
            "final_word_count", "final_character_count", "created_at", "updated_at",
        ]

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username
