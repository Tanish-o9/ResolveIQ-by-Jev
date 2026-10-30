"""Mock Action Simulator: Tool execution for Stripe refunds, Auth0 password resets, and session unlocking."""
from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class ActionResult:
    success: bool
    action_type: str
    action_id: str
    message: str
    details: dict[str, Any]
    executed_at: str


def _gen_id(prefix: str, length: int = 16) -> str:
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return f"{prefix}_{suffix}"


def execute_stripe_refund(ticket_id: int, customer_email: str, amount_usd: float = 29.00, reason: str = "duplicate_charge") -> ActionResult:
    """Executes a simulated Stripe refund and generates receipt data."""
    refund_id = _gen_id("re_3Nx")
    charge_id = _gen_id("ch_3Nx")

    return ActionResult(
        success=True,
        action_type="stripe_refund",
        action_id=refund_id,
        message=f"Successfully refunded ${amount_usd:.2f} USD to customer ({customer_email or 'primary card'}).",
        details={
            "refund_id": refund_id,
            "charge_id": charge_id,
            "amount_refunded": f"${amount_usd:.2f}",
            "currency": "usd",
            "status": "succeeded",
            "reason": reason,
            "receipt_url": f"https://dashboard.stripe.com/test/refunds/{refund_id}",
        },
        executed_at=datetime.now(timezone.utc).isoformat(),
    )


def execute_auth0_password_reset(ticket_id: int, customer_email: str) -> ActionResult:
    """Dispatches a simulated Auth0 password reset ticket."""
    ticket_url_id = _gen_id("auth0_reset")
    email = customer_email or "customer@workspace.com"

    return ActionResult(
        success=True,
        action_type="auth0_password_reset",
        action_id=ticket_url_id,
        message=f"Password reset ticket generated and securely dispatched to {email}.",
        details={
            "ticket_url": f"https://auth.company.com/u/reset-password?ticket={ticket_url_id}",
            "expires_in": "24 hours",
            "dispatched_to": email,
            "sso_claim_refreshed": True,
        },
        executed_at=datetime.now(timezone.utc).isoformat(),
    )


def execute_session_unlock(ticket_id: int, customer_email: str) -> ActionResult:
    """Clears stale SSO session tokens and triggers an automatic workspace re-invitation."""
    session_id = _gen_id("sess_unlock")
    email = customer_email or "customer@workspace.com"

    return ActionResult(
        success=True,
        action_type="session_unlock",
        action_id=session_id,
        message=f"Invalidated stale OAuth tokens and re-sent corporate invite to {email}.",
        details={
            "session_id": session_id,
            "email": email,
            "action": "reinvite_sent",
            "token_status": "revoked_and_reissued",
        },
        executed_at=datetime.now(timezone.utc).isoformat(),
    )

