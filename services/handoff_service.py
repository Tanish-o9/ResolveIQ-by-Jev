"""Multi-Agent Escalation Hand-off: Generates confidential internal briefing notes for human specialist teams."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SpecialistHandoffNote:
    target_specialist_team: str
    priority_level: str
    customer_value_context: str
    recommended_action: str
    briefing_markdown: str


def generate_specialist_handoff(
    ticket_id: int,
    customer_name: str,
    customer_tier: str,
    ltv: float,
    department: str,
    urgency_score: float,
    churn_risk: float,
    rule_reason: str,
) -> SpecialistHandoffNote:
    """Generates internal handoff documentation for cross-agent specialist routing."""
    dept_lower = department.lower()
    if dept_lower == "billing":
        team = "Senior Billing Operations & Finance"
        rec = "Review transaction history, verify idempotency, and execute Stripe refund or credit adjustment."
    elif dept_lower == "technical":
        team = "Tier 3 Infrastructure & DevOps On-Call"
        rec = "Inspect telemetry logs, verify API rate limits, and check worker connection pool."
    elif dept_lower == "account":
        team = "Identity, SSO & Account Security Lead"
        rec = "Validate admin identity, verify SSO domain claim, and manually re-issue workspace invite."
    else:
        team = "Senior Customer Success Lead"
        rec = "Schedule priority follow-up call with customer."

    priority = "CRITICAL (P1)" if (urgency_score >= 2.5 or customer_tier == "Enterprise") else "HIGH (P2)"
    churn_tag = "⚠️ CHURN THREAT ACTIVE" if churn_risk >= 0.6 else "Normal Account Health"

    briefing = (
        f"🔒 **CONFIDENTIAL SPECIALIST BRIEFING: TICKET #{ticket_id}**\n\n"
        f"- **Assigned Team:** {team}\n"
        f"- **Priority Rating:** {priority} | **Account Status:** {churn_tag}\n"
        f"- **Customer Profile:** {customer_name} ({customer_tier} Tier | LTV: ${ltv:,.2f})\n"
        f"- **Triage Assessment:** Urgency {urgency_score:.2f}/3.0 | Trigger: {rule_reason}\n"
        f"- **Action Protocol:** {rec}\n"
        f"- **Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    return SpecialistHandoffNote(
        target_specialist_team=team,
        priority_level=priority,
        customer_value_context=f"{customer_tier} Tier (LTV: ${ltv:,.2f})",
        recommended_action=rec,
        briefing_markdown=briefing,
    )
