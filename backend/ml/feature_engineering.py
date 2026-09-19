"""
Builds a flat feature vector describing a submission's writing activity,
for use by anomaly_detection.py. Every feature here is a Layer-2 "derived"
measurement (see spec section 97) - none of it is a raw OS-level
observation, and none of it is itself an accusation.
"""
import numpy as np


def build_features(events_df, snapshots_df, sessions_df) -> dict:
    features = {}

    # Writing / timing features
    features["session_count"] = len(sessions_df) if sessions_df is not None else 0
    features["total_active_seconds"] = (
        sessions_df["active_seconds"].sum() if sessions_df is not None and len(sessions_df) else 0
    )
    features["total_idle_seconds"] = (
        sessions_df["idle_seconds"].sum() if sessions_df is not None and len(sessions_df) else 0
    )

    if events_df is None or len(events_df) == 0:
        features.update({
            "insertion_count": 0, "large_insertion_count": 0, "avg_insertion_size": 0.0,
            "max_insertion_size": 0, "deletion_count": 0, "replacement_count": 0,
            "pct_words_from_large_insertions": 0.0, "longest_inactivity_seconds": 0,
        })
        return features

    insertions = events_df[events_df["event_type"].isin(["insertion", "large_insertion"])]
    large_insertions = events_df[events_df["event_type"] == "large_insertion"]
    deletions = events_df[events_df["event_type"].isin(["deletion", "large_deletion"])]
    replacements = events_df[events_df["event_type"] == "replacement"]
    idle_events = events_df[events_df["event_type"] == "idle_started"]

    total_inserted_words = insertions["words_affected"].sum() if len(insertions) else 0
    large_inserted_words = large_insertions["words_affected"].sum() if len(large_insertions) else 0

    features.update({
        "insertion_count": len(insertions),
        "large_insertion_count": len(large_insertions),
        "avg_insertion_size": float(insertions["words_affected"].mean()) if len(insertions) else 0.0,
        "max_insertion_size": int(insertions["words_affected"].max()) if len(insertions) else 0,
        "deletion_count": len(deletions),
        "replacement_count": len(replacements),
        "pct_words_from_large_insertions": (
            float(large_inserted_words / total_inserted_words) if total_inserted_words else 0.0
        ),
        "longest_inactivity_seconds": (
            max((m.get("gap_seconds", 0) for m in idle_events.get("metadata", []) if isinstance(m, dict)), default=0)
            if len(idle_events) else 0
        ),
    })
    return features


def features_to_vector(features: dict) -> np.ndarray:
    keys = sorted(features.keys())
    return np.array([[features[k] for k in keys]], dtype=float), keys
