"""Customer 360 CRM profile retrieval and account health enrichment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CustomerProfile:
    name: str
    email: str
    company: str
    tier: str
    monthly_recurring_revenue: float
    lifetime_value: float
    renewal_days_left: int
    account_manager: str
    total_past_tickets: int
    open_tickets: int
    health_status: str  # "Healthy", "At Risk", "Critical Churn Threat"


MOCK_CRM_PROFILES: dict[str, CustomerProfile] = {
    "sarah jenkins": CustomerProfile(
        name="Sarah Jenkins",
        email="sarah.jenkins@fintechpro.io",
        company="FintechPro Corp",
        tier="Pro",
        monthly_recurring_revenue=149.00,
        lifetime_value=2380.00,
        renewal_days_left=8,
        account_manager="Marcus Vance",
        total_past_tickets=3,
        open_tickets=1,
        health_status="Critical Churn Threat",
    ),
    "alex chen": CustomerProfile(
        name="Alex Chen",
        email="alex.chen@cloudscale.net",
        company="CloudScale Logistics",
        tier="Enterprise",
        monthly_recurring_revenue=1200.00,
        lifetime_value=14400.00,
        renewal_days_left=45,
        account_manager="Elena Rostova (VP Accounts)",
        total_past_tickets=6,
        open_tickets=2,
        health_status="Healthy",
    ),
    "marcus vance": CustomerProfile(
        name="Marcus Vance",
        email="marcus.v@analytics.dev",
        company="Vance Analytics",
        tier="Free",
        monthly_recurring_revenue=0.00,
        lifetime_value=0.00,
        renewal_days_left=0,
        account_manager="Self-serve Queue",
        total_past_tickets=1,
        open_tickets=1,
        health_status="Healthy",
    ),
    "amit sharma": CustomerProfile(
        name="Amit Sharma",
        email="amit.sharma@payflow.in",
        company="Payflow India",
        tier="Pro",
        monthly_recurring_revenue=99.00,
        lifetime_value=890.00,
        renewal_days_left=14,
        account_manager="Priya Patel",
        total_past_tickets=2,
        open_tickets=1,
        health_status="At Risk",
    ),
}


def get_customer_crm_profile(name_or_email: str, default_tier: str = "Pro") -> CustomerProfile:
    """Retrieves existing CRM record or synthesizes account profile for anonymous customers."""
    lookup_key = name_or_email.strip().lower()

    for key, profile in MOCK_CRM_PROFILES.items():
        if key in lookup_key or profile.email.lower() in lookup_key:
            return profile

    # Synthesize realistic profile for new customer
    clean_name = name_or_email.strip().title() if name_or_email else "Anonymous Customer"
    is_enterprise = default_tier.lower() == "enterprise"

    return CustomerProfile(
        name=clean_name,
        email=f"{clean_name.lower().replace(' ', '.')}@company.com",
        company=f"{clean_name.split()[0]} Systems Inc." if len(clean_name.split()) > 0 else "Client Corp",
        tier=default_tier.title(),
        monthly_recurring_revenue=899.00 if is_enterprise else 49.00,
        lifetime_value=5400.00 if is_enterprise else 390.00,
        renewal_days_left=60 if is_enterprise else 22,
        account_manager="Dedicated Solutions Lead" if is_enterprise else "Tier 1 Specialist Rotation",
        total_past_tickets=1,
        open_tickets=1,
        health_status="Healthy",
    )

