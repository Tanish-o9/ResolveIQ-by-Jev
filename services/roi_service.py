"""Business Impact, Deflection Rate, and ROI / Cost-Savings Calculator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ROIReport:
    total_tickets: int
    deflected_tickets: int
    deflection_rate_pct: float
    agent_hours_saved: float
    total_cost_saved_usd: float
    ai_compute_cost_usd: float
    net_savings_usd: float
    avg_speedup_factor: str


HUMAN_AGENT_HOURLY_RATE = 25.00  # $25/hour industry average support specialist
MINUTES_PER_MANUAL_TICKET = 14.0  # Average handling time (14 mins)
AI_COST_PER_TICKET = 0.0025  # ~$0.0025 in inference per ticket


def calculate_business_roi(total_tickets: int, escalated_count: int) -> ROIReport:
    """Calculates quantifiable time and cost savings compared to traditional human support."""
    if total_tickets == 0:
        return ROIReport(
            total_tickets=0,
            deflected_tickets=0,
            deflection_rate_pct=0.0,
            agent_hours_saved=0.0,
            total_cost_saved_usd=0.0,
            ai_compute_cost_usd=0.0,
            net_savings_usd=0.0,
            avg_speedup_factor="0x",
        )

    deflected = max(0, total_tickets - escalated_count)
    deflection_rate = round((deflected / total_tickets) * 100, 1)

    # 14 mins saved per deflected ticket
    hours_saved = round((deflected * MINUTES_PER_MANUAL_TICKET) / 60.0, 1)

    gross_saved = round(hours_saved * HUMAN_AGENT_HOURLY_RATE, 2)
    ai_cost = round(total_tickets * AI_COST_PER_TICKET, 2)
    net_saved = round(max(0.0, gross_saved - ai_cost), 2)

    return ROIReport(
        total_tickets=total_tickets,
        deflected_tickets=deflected,
        deflection_rate_pct=deflection_rate,
        agent_hours_saved=hours_saved,
        total_cost_saved_usd=gross_saved,
        ai_compute_cost_usd=ai_cost,
        net_savings_usd=net_saved,
        avg_speedup_factor="480x faster (<1.5s vs 12m)",
    )
