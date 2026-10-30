"""Branded HTML email dispatcher and preview generator for support ticket resolutions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_branded_resolution_email(
    ticket_id: int,
    customer_name: str,
    subject: str,
    body_text: str,
    sla_hours: int,
    department: str,
) -> dict[str, Any]:
    """Generates an HTML email preview and delivery confirmation payload."""
    clean_name = customer_name or "Valued Customer"
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #1e293b; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .email-header {{ background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 24px; color: #ffffff; }}
        .email-header h2 {{ margin: 0 0 6px 0; font-size: 20px; }}
        .email-header p {{ margin: 0; font-size: 13px; opacity: 0.9; }}
        .email-body {{ padding: 24px; font-size: 14px; line-height: 1.6; color: #334155; }}
        .resolution-box {{ background: #f8fafc; border-left: 4px solid #6366f1; padding: 14px 18px; margin: 18px 0; border-radius: 0 6px 6px 0; font-size: 14px; }}
        .email-meta {{ display: flex; gap: 16px; margin-top: 20px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; }}
        .email-footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="email-header">
          <h2>ResolveIQ Support Resolution</h2>
          <p>Ticket #{ticket_id} • {department.title()} Team</p>
        </div>
        <div class="email-body">
          <p>Hi {clean_name},</p>
          <p>Thank you for contacting our support team. We have triaged and processed your request:</p>
          <div class="resolution-box">
            {body_text.replace(chr(10), '<br/>')}
          </div>
          <p>If you have any further questions or if this does not fully resolve your inquiry, simply reply directly to this email to re-open the thread.</p>
          <div class="email-meta">
            <span><strong>Target SLA:</strong> {sla_hours} Hours</span>
            <span><strong>Processed At:</strong> {now_str}</span>
          </div>
        </div>
        <div class="email-footer">
          <p>&copy; 2026 ResolveIQ Cloud Systems. All rights reserved.</p>
        </div>
      </div>
    </body>
    </html>
    """

    return {
        "status": "delivered",
        "ticket_id": ticket_id,
        "recipient": customer_name,
        "subject": subject or f"[Resolved] Ticket #{ticket_id} Support Resolution",
        "html": html_content,
        "dispatched_at": datetime.now(timezone.utc).isoformat(),
    }

