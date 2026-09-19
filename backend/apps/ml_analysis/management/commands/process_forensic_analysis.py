"""
python manage.py process_forensic_analysis [--submission-id N]

Simple synchronous background-job stand-in for the first SQLite version
(section 68). Computes features per submission and stores an MLAnalysis
row. Designed to later be dropped into a Celery task with no change to
the underlying logic.
"""
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand

from apps.events.models import ForensicEvent
from apps.ml_analysis.models import MLAnalysis
from apps.sessions.models import WritingSession
from apps.submissions.models import Submission
from ml.anomaly_detection import IsolationForestAnalyzer
from ml.feature_engineering import build_features


def make_json_serializable(val):
    """Recursively convert numpy types to standard Python types for JSON fields."""
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64)):
        return float(val)
    elif isinstance(val, np.ndarray):
        return val.tolist()
    elif isinstance(val, dict):
        return {str(k): make_json_serializable(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [make_json_serializable(v) for v in val]
    return val


class Command(BaseCommand):
    help = "Run ML forensic analysis for submissions and store MLAnalysis results."

    def add_arguments(self, parser):
        parser.add_argument("--submission-id", type=int, default=None)

    def handle(self, *args, **options):
        submissions = Submission.objects.all()
        if options["submission_id"]:
            submissions = submissions.filter(id=options["submission_id"])

        analyzer = IsolationForestAnalyzer()

        for submission in submissions:
            events = list(ForensicEvent.objects.filter(submission=submission).values(
                "event_type", "words_affected", "characters_affected", "metadata"
            ))
            sessions = list(WritingSession.objects.filter(submission=submission).values(
                "active_seconds", "idle_seconds"
            ))
            events_df = pd.DataFrame(events) if events else pd.DataFrame(
                columns=["event_type", "words_affected", "characters_affected", "metadata"]
            )
            sessions_df = pd.DataFrame(sessions) if sessions else pd.DataFrame(
                columns=["active_seconds", "idle_seconds"]
            )

            features = build_features(events_df, None, sessions_df)
            insertion_sizes = (
                events_df[events_df["event_type"].isin(["insertion", "large_insertion"])]["words_affected"].tolist()
                if len(events_df) else []
            )
            result = analyzer.analyze(features, insertion_sizes=insertion_sizes)

            # Sanitize features and results for JSON serialization and scoring
            clean_features = make_json_serializable(features)
            clean_result = make_json_serializable(result)

            anomaly_score = float(clean_result.get("anomaly_score", 0.0))
            total_idle = float(clean_features.get("total_idle_seconds", 0))
            large_ins = int(clean_features.get("large_insertion_count", 0))
            repl_count = int(clean_features.get("replacement_count", 0))
            ins_count = int(clean_features.get("insertion_count", 0))

            MLAnalysis.objects.create(
                submission=submission,
                anomaly_score=anomaly_score,
                writing_pattern_score=min(1.0, total_idle / 3600),
                insertion_pattern_score=min(1.0, large_ins / 5),
                editing_pattern_score=min(1.0, repl_count / 10),
                analysis_summary=(
                    f"{len(clean_result.get('signals', []))} indicator(s) generated from "
                    f"{ins_count} insertion event(s)."
                ),
                feature_data=clean_features,
                signals=clean_result.get("signals", []),
            )
            self.stdout.write(self.style.SUCCESS(
                f"Analyzed submission {submission.id}: anomaly_score={anomaly_score}"
            ))