"""Automated Bug Trend Clustering & Engineering Incident / Jira Issue Generator."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class IncidentSpike:
    topic: str
    severity: str  # "P1 (Critical Outage)", "P2 (Feature Degraded)", "P3 (Minor)"
    affected_tickets_count: int
    detected_pattern: str
    sample_quotes: list[str]
    suggested_jira_issue: dict[str, str]


PATTERNS = [
    {
        "topic": "CSV Export Timeout & Failure",
        "keywords": ["csv", "export", "download", "report", "hangs"],
        "severity": "P2 (Feature Degraded)",
        "summary": "Fix CSV background report generation timeout on large datasets",
        "component": "Reporting Engine / Data Pipelines",
    },
    {
        "topic": "Duplicate Billing / Stripe Webhook Race Condition",
        "keywords": ["charged twice", "duplicate", "invoice", "double charge"],
        "severity": "P1 (Financial Risk)",
        "summary": "Investigate idempotency key failure causing duplicate subscription renewals",
        "component": "Billing Service / Stripe Integration",
    },
    {
        "topic": "Corporate SSO / OAuth Session Invalidation",
        "keywords": ["sso", "admin changed email", "cannot access workspace", "login failed"],
        "severity": "P2 (Access Blocker)",
        "summary": "Handle corporate email updates without invalidating existing team workspace sessions",
        "component": "Auth / Identity Service",
    },
    {
        "topic": "Outbound Webhook Delivery Failures",
        "keywords": ["webhook", "stopped delivering", "events", "syncing halted", "outage"],
        "severity": "P1 (Critical Outage)",
        "summary": "Outbound webhook event dispatcher worker queue connection timeout",
        "component": "Infrastructure / Worker Daemons",
    },
]


def detect_incident_spikes(tickets: list[dict[str, Any]]) -> list[IncidentSpike]:
    """Analyzes recent tickets in database to detect active incident clusters."""
    spikes: list[IncidentSpike] = []

    for pattern in PATTERNS:
        matches = []
        for t in tickets:
            text = (t.get("ticket_text") or "").lower()
            if any(kw in text for kw in pattern["keywords"]):
                matches.append(t.get("ticket_text", "")[:120])

        if len(matches) >= 1:
            jira_body = (
                f"### Incident Report: {pattern['topic']}\n\n"
                f"**Severity:** {pattern['severity']}\n"
                f"**Component:** {pattern['component']}\n"
                f"**Customer Impact:** {len(matches)} active customer support tickets linked\n\n"
                f"#### Sample Customer Reports:\n"
                + "\n".join(f"- *\"{m}...\"*" for m in matches[:3])
                + "\n\n#### Recommended Engineering Action:\n"
                "- Check database query locks and worker queue health.\n"
                "- Verify idempotency keys and error logs in Sentry/Datadog.\n"
                "- Prepare hotfix patch release."
            )

            spikes.append(
                IncidentSpike(
                    topic=pattern["topic"],
                    severity=pattern["severity"],
                    affected_tickets_count=len(matches),
                    detected_pattern=", ".join(pattern["keywords"][:3]),
                    sample_quotes=matches[:2],
                    suggested_jira_issue={
                        "title": f"[{pattern['severity']}] {pattern['summary']}",
                        "body": jira_body,
                        "component": pattern["component"],
                    },
                )
            )

    return spikes

