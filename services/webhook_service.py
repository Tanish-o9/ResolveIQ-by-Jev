"""Real-time Slack / Discord Webhook notification dispatcher for critical SLAs and churn alerts."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("resolveiq-by-jev")


def dispatch_slack_alert(
    ticket_id: int,
    customer_name: str,
    customer_tier: str,
    department: str,
    urgency_score: float,
    rule_reason: str,
    sla_hours: int,
    sentiment: str,
) -> dict[str, Any]:
    """Sends a formatted notification to a configured Slack or Discord webhook, or logs simulated alert."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()

    payload = {
        "text": f"🚨 *[ResolveIQ Alert]* High-Priority Ticket #{ticket_id} Requires Immediate Review",
        "attachments": [
            {
                "color": "#ef4444" if urgency_score >= 2.5 else "#f59e0b",
                "fields": [
                    {"title": "Customer", "value": f"{customer_name} ({customer_tier} Tier)", "short": True},
                    {"title": "Department", "value": department.title(), "short": True},
                    {"title": "Urgency Rubric", "value": f"{urgency_score:.2f} / 3.0", "short": True},
                    {"title": "SLA Deadline", "value": f"{sla_hours} Hours", "short": True},
                    {"title": "Sentiment", "value": sentiment, "short": True},
                    {"title": "Escalation Reason", "value": rule_reason, "short": False},
                ],
                "footer": "ResolveIQ-by-Jev Triage Engine",
            }
        ],
    }

    if webhook_url and webhook_url.startswith("http"):
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.post(webhook_url, json=payload)
                return {
                    "dispatched": True,
                    "target": "live_webhook",
                    "status_code": res.status_code,
                    "payload": payload,
                }
        except Exception as exc:
            logger.warning(f"Failed to post to live Slack webhook: {exc}")
            return {
                "dispatched": False,
                "target": "live_webhook",
                "error": str(exc),
                "payload": payload,
            }

    # Simulated fallback for local demo
    return {
        "dispatched": True,
        "target": "simulated_slack_channel (#support-urgent)",
        "payload": payload,
    }

