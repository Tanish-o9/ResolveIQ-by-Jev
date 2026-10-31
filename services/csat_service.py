"""Customer Satisfaction (CSAT) Prediction and Post-Resolution Feedback."""
from __future__ import annotations


def predict_csat_score(urgency_score: float, sentiment_mood: str, needs_human: bool) -> int:
    """Predicts expected customer satisfaction (1 to 5 stars) based on incident signals."""
    if "Angry" in sentiment_mood:
        return 2 if needs_human else 3
    elif "Frustrated" in sentiment_mood:
        return 3
    elif urgency_score < 1.0:
        return 5
    return 4

