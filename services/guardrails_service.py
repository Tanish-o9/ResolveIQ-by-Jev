"""Enterprise PII Masking & Data Privacy Guardrails (SOC-2 / GDPR Compliant)."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GuardrailsReport:
    has_pii: bool
    sanitized_text: str
    redacted_items: list[str]


# Common PII Regex Patterns
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
API_KEY_PATTERN = re.compile(r"\b(?:sk_[a-zA-Z0-9_\-]{20,}|ghp_[a-zA-Z0-9]{20,}|key-[a-zA-Z0-9]{20,})\b")
PASSWORD_PATTERN = re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*([^\s,;]+)")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b")


def sanitize_ticket_pii(text: str) -> GuardrailsReport:
    """Scans and redacts sensitive PII before sending to LLM or database."""
    redacted = []
    sanitized = text

    # 1. Credit Cards
    if CREDIT_CARD_PATTERN.search(sanitized):
        def _mask_card(m):
            raw = re.sub(r"[ -]", "", m.group(0))
            last4 = raw[-4:]
            return f"[REDACTED_CARD: ****-****-****-{last4}]"
        sanitized = CREDIT_CARD_PATTERN.sub(_mask_card, sanitized)
        redacted.append("Credit Card Number")

    # 2. Secret API Keys
    if API_KEY_PATTERN.search(sanitized):
        sanitized = API_KEY_PATTERN.sub("[REDACTED_API_SECRET]", sanitized)
        redacted.append("API Secret Key")

    # 3. Passwords
    if PASSWORD_PATTERN.search(sanitized):
        sanitized = PASSWORD_PATTERN.sub(r"password: [REDACTED_PASSWORD]", sanitized)
        redacted.append("Plaintext Password")

    # 4. Social Security Numbers
    if SSN_PATTERN.search(sanitized):
        sanitized = SSN_PATTERN.sub("[REDACTED_SSN]", sanitized)
        redacted.append("Social Security Number (SSN)")

    # 5. Phone numbers
    if PHONE_PATTERN.search(sanitized):
        sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)
        redacted.append("Personal Phone Number")

    return GuardrailsReport(
        has_pii=len(redacted) > 0,
        sanitized_text=sanitized,
        redacted_items=redacted,
    )
