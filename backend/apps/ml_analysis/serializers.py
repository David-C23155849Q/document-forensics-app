from rest_framework import serializers

from .models import MLAnalysis


class MLAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLAnalysis
        fields = [
            "id", "submission", "model_version", "anomaly_score", "writing_pattern_score",
            "insertion_pattern_score", "editing_pattern_score", "authorship_consistency_indicator",
            "analysis_summary", "signals", "created_at",
        ]
