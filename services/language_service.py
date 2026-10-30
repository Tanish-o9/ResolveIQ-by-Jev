"""Language detection and multi-lingual prompt conditioning."""
from __future__ import annotations

import re


LANGUAGE_INDICATORS = {
    "Hindi / Hinglish": [
        "kripya", "mujhe", "paisa", "paise", "kaam", "nahi", "kar", "raha", "hai", "karo", "madad", "mera", "meri", "refund chahiye", "login nahi ho raha"
    ],
    "Spanish": [
        "hola", "por favor", "gracias", "ayuda", "cuenta", "factura", "problema", "reembolso", "urgente"
    ],
    "French": [
        "bonjour", "s'il vous plaît", "merci", "aide", "compte", "facturation", "problème", "remboursement"
    ],
    "German": [
        "hallo", "bitte", "danke", "hilfe", "konto", "rechnung", "problem", "rückerstattung"
    ],
}


def detect_language(text: str) -> str:
    """Detects primary language based on common conversational tokens."""
    lowered = text.lower()

    # Check Devanagari script for direct Hindi
    if re.search(r"[\u0900-\u097F]", text):
        return "Hindi (Devanagari)"

    # Check keyword tokens
    for lang, markers in LANGUAGE_INDICATORS.items():
        if any(re.search(r"\b" + re.escape(m) + r"\b", lowered) for m in markers):
            return lang

    return "English"

