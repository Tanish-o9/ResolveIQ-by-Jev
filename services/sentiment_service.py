"""Customer sentiment analysis, frustration detection, and churn risk estimation."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SentimentResult:
    mood: str  # "Calm", "Neutral", "Frustrated", "Angry (High Churn Risk)"
    churn_risk_score: float  # 0.0 to 1.0
    retention_playbook: str | None
    detected_signals: list[str]


ANGRY_SIGNALS = [
    "cancel", "cancelling", "refund immediately", "terrible", "worst",
    "lawsuit", "legal", "unacceptable", "closing the books", "switching to",
    "waste of money", "disaster", "horrible", "fed up", "chargeback"
]

FRUSTRATED_SIGNALS = [
    "broken", "failed", "again", "still not working", "slow", "urgent",
    "waiting", "stuck", "frustrated", "buggy", "asap", "disappointed"
]

CALM_SIGNALS = [
    "please", "thank you", "thanks", "curious", "how do i", "wondering", "appreciate"
]


def analyze_sentiment(text: str) -> SentimentResult:
    normalized = text.lower()
    signals: list[str] = []

    # Check for angry/churn triggers
    angry_matches = [s for s in ANGRY_SIGNALS if s in normalized]
    frustrated_matches = [s for s in FRUSTRATED_SIGNALS if s in normalized]
    calm_matches = [s for s in CALM_SIGNALS if s in normalized]

    if angry_matches:
        signals.extend(angry_matches)
        churn_risk = min(0.95, 0.65 + (len(angry_matches) * 0.1))
        mood = "Angry (High Churn Risk)"
        playbook = (
            "Retention Playbook Active: Offer immediate 20% renewal courtesy discount, "
            "waive disputed fee, and assign dedicated account lead."
        )
    elif frustrated_matches:
        signals.extend(frustrated_matches)
        churn_risk = min(0.60, 0.30 + (len(frustrated_matches) * 0.08))
        mood = "Frustrated"
        playbook = (
            "Standard De-escalation: Prioritize root cause fix, apologize for delay, "
            "and provide explicit timeline."
        )
    else:
        signals.extend(calm_matches)
        churn_risk = 0.10
        mood = "Calm"
        playbook = None

    return SentimentResult(
        mood=mood,
        churn_risk_score=round(churn_risk, 2),
        retention_playbook=playbook,
        detected_signals=signals[:4],
    )

