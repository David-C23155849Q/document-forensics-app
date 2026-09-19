"""
Anomaly detection. Defines a common ForensicAnalyzer interface so the
underlying model can be swapped later (e.g. for an AdvancedSequenceAnalyzer)
without touching calling code.

All output is descriptive ("unusual insertion event") and explicitly NOT a
probability of academic misconduct - see docs/forensic-methodology.md.
"""
from abc import ABC, abstractmethod

import numpy as np
from sklearn.ensemble import IsolationForest


class ForensicAnalyzer(ABC):
    @abstractmethod
    def analyze(self, features: dict) -> dict:
        """Return {"anomaly_score": float 0-1, "signals": [...]}"""
        raise NotImplementedError


class IsolationForestAnalyzer(ForensicAnalyzer):
    """
    Single-submission anomaly detection using simple statistical thresholds
    combined with an IsolationForest fit on the submission's own event-level
    insertion sizes (its own baseline), since we typically won't have a
    large cross-student training set in the first version.
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state

    def analyze(self, features: dict, insertion_sizes: list | None = None) -> dict:
        signals = []
        anomaly_score = 0.0

        insertion_sizes = insertion_sizes or []
        if len(insertion_sizes) >= 4:
            arr = np.array(insertion_sizes).reshape(-1, 1)
            model = IsolationForest(contamination=self.contamination, random_state=self.random_state)
            model.fit(arr)
            scores = model.decision_function(arr)  # higher = more normal
            preds = model.predict(arr)  # -1 = anomaly
            for size, score, pred in zip(insertion_sizes, scores, preds):
                if pred == -1:
                    normalized = float(np.clip((0.5 - score) * 1.5, 0, 1))
                    anomaly_score = max(anomaly_score, normalized)
                    signals.append({
                        "type": "large_insertion",
                        "severity": "high" if normalized > 0.7 else "medium",
                        "description": (
                            f"Insertion of {size} words is substantially larger than this "
                            "submission's typical insertion pattern."
                        ),
                    })
        elif features.get("max_insertion_size", 0) >= 100:
            anomaly_score = 0.6
            signals.append({
                "type": "large_insertion",
                "severity": "medium",
                "description": "A large insertion was recorded; insufficient history for full baseline comparison.",
            })

        if features.get("longest_inactivity_seconds", 0) >= 600:
            signals.append({
                "type": "extended_inactivity",
                "severity": "low",
                "description": "An extended inactivity period was recorded. This is not necessarily unusual.",
            })

        if features.get("pct_words_from_large_insertions", 0) >= 0.5:
            anomaly_score = max(anomaly_score, 0.5)
            signals.append({
                "type": "insertion_dominant_writing",
                "severity": "medium",
                "description": "A large proportion of the final word count originated from large insertions.",
            })

        return {"anomaly_score": round(anomaly_score, 2), "signals": signals}
