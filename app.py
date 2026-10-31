from __future__ import annotations

import csv
import io
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

ssl_cert_file = os.getenv("SSL_CERT_FILE")
if ssl_cert_file and not Path(ssl_cert_file).exists():
    os.environ.pop("SSL_CERT_FILE", None)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from services.jev_service import analyze_ticket, JevDecision
from services.response_chain import draft_reply, stream_draft_reply
from services.knowledge_service import search_knowledge_base
from services.sentiment_service import analyze_sentiment
from services.language_service import detect_language
from services.webhook_service import dispatch_slack_alert
from services.crm_service import get_customer_crm_profile
from services.audio_service import transcribe_audio_file
from services.cluster_service import detect_incident_spikes
from services.email_service import generate_branded_resolution_email
from services.guardrails_service import sanitize_ticket_pii
from services.roi_service import calculate_business_roi
from services.csat_service import predict_csat_score
from services.eval_service import run_model_benchmark
from services.action_service import (
    execute_stripe_refund,
    execute_auth0_password_reset,
    execute_session_unlock,
)
from services.copilot_service import tune_response_tone
from services.handoff_service import generate_specialist_handoff
from services.db import (
    init_db,
    save_ticket,
    get_tickets,
    get_ticket,
    update_ticket,
    get_analytics_summary,
    add_ticket_message,
    get_ticket_messages,
    record_action_taken,
    record_csat_feedback,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resolveiq-by-jev")

init_db()

app = FastAPI(
    title="ResolveIQ-by-Jev",
    version="2.3.0",
    description="Autonomous Enterprise Support Triage with Calibrated Jev, PII Guardrails, ROI Analytics & CSAT Loops",
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class TicketRequest(BaseModel):
    ticket: str = Field(min_length=5, max_length=8000)
    customer_name: str = Field(default="Anonymous")
    customer_email: str = Field(default="")
    customer_tier: str = Field(default="Pro")


class TicketUpdateRequest(BaseModel):
    status: str | None = None
    final_reply: str | None = None
    override_department: str | None = None


class ActionExecuteRequest(BaseModel):
    action_type: str
    amount: float = 29.0
    reason: str = "customer_support_triage"


class FollowupMessageRequest(BaseModel):
    sender: str = "customer"
    message: str = Field(min_length=2, max_length=4000)


class EmailDispatchRequest(BaseModel):
    subject: str = ""
    body: str = ""


class CSATRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: str = ""


class BatchItem(BaseModel):
    ticket: str
    customer_name: str = "Customer"
    customer_tier: str = "Pro"


class BatchRequest(BaseModel):
    items: list[BatchItem]


class ToneTuneRequest(BaseModel):
    text: str = Field(min_length=5)
    tone: str = Field(default="formal")
    customer_name: str = "Customer"


class IncomingWebhookPayload(BaseModel):
    source: str = "custom"
    ticket_text: str = Field(min_length=5)
    customer_name: str = "Anonymous"
    customer_email: str = ""
    customer_tier: str = "Pro"


def choose_route(
    department: str,
    dept_conf: float,
    urgency: float,
    human_prob: float,
    customer_tier: str = "Pro",
    churn_risk: float = 0.1,
) -> tuple[str, bool, str, int]:
    tier = customer_tier.title()
    is_enterprise = tier == "Enterprise"

    if urgency >= 2.5:
        base_sla = 2
    elif urgency >= 1.8:
        base_sla = 4
    elif urgency >= 1.0:
        base_sla = 12
    else:
        base_sla = 24

    sla_hours = max(1, base_sla // 2) if is_enterprise else base_sla

    reasons = []
    if human_prob >= 0.65:
        reasons.append("High human review risk flag")
    if dept_conf < 0.60:
        reasons.append("Low department confidence")
    if urgency >= 2.5:
        reasons.append("Critical urgency score")
    if is_enterprise and urgency >= 1.8:
        reasons.append("Enterprise VIP SLA escalation")
    if churn_risk >= 0.70:
        reasons.append("High customer churn / cancellation threat")

    needs_human = len(reasons) > 0

    if needs_human:
        route = f"{department.title()} → Specialist Tier"
        rule_reason = "; ".join(reasons)
    else:
        route = f"{department.title()} Standard Queue"
        rule_reason = f"Standard queue routing (Confidence: {round(dept_conf * 100)}%)"

    return route, needs_human, rule_reason, sla_hours


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/portal", response_class=HTMLResponse)
def customer_portal(request: Request):
    return templates.TemplateResponse(request=request, name="portal.html", context={})


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.post("/api/analyze")
def analyze(payload: TicketRequest):
    raw_ticket = payload.ticket.strip()

    # 1. PII Redaction Guardrails
    pii_report = sanitize_ticket_pii(raw_ticket)
    safe_ticket = pii_report.sanitized_text

    try:
        decision = analyze_ticket(safe_ticket)
    except Exception as exc:
        logger.exception("Jev analysis failed")
        raise HTTPException(status_code=502, detail=f"Jev API error: {exc}") from exc

    detected_lang = detect_language(safe_ticket)
    sentiment_data = analyze_sentiment(safe_ticket)
    crm = get_customer_crm_profile(payload.customer_name or payload.customer_email, payload.customer_tier)

    route, needs_human, rule_reason, sla_hours = choose_route(
        decision.department,
        decision.department_confidence,
        decision.urgency_score,
        decision.human_review_probability,
        customer_tier=payload.customer_tier,
        churn_risk=sentiment_data.churn_risk_score,
    )

    predicted_csat = predict_csat_score(decision.urgency_score, sentiment_data.mood, needs_human)

    articles = search_knowledge_base(safe_ticket, top_k=2)
    knowledge_snippets = [f"{a.title}: {a.content}" for a in articles]

    try:
        reply = draft_reply(
            safe_ticket,
            decision,
            route,
            customer_tier=payload.customer_tier,
            knowledge_snippets=knowledge_snippets,
            customer_language=detected_lang,
            sentiment=sentiment_data.mood,
            retention_guidance=sentiment_data.retention_playbook,
        )
    except Exception as exc:
        logger.exception("Reply generation failed")
        reply = f"Jev analysis completed. Draft generation fallback: {exc}"

    handoff_brief = None
    if needs_human or decision.urgency_score >= 1.8 or crm.tier == "Enterprise":
        handoff_obj = generate_specialist_handoff(
            ticket_id=0,
            customer_name=crm.name,
            customer_tier=crm.tier,
            ltv=crm.lifetime_value,
            department=decision.department,
            urgency_score=decision.urgency_score,
            churn_risk=sentiment_data.churn_risk_score,
            rule_reason=rule_reason,
        )
        handoff_brief = handoff_obj.briefing_markdown

    ticket_id = save_ticket(
        ticket_text=safe_ticket,
        department=decision.department,
        department_confidence=decision.department_confidence,
        urgency_score=decision.urgency_score,
        urgency_confidence=decision.urgency_confidence,
        refund_probability=decision.refund_probability,
        human_review_probability=decision.human_review_probability,
        route=route,
        needs_human=needs_human,
        rule_reason=rule_reason,
        sla_deadline_hours=sla_hours,
        suggested_reply=reply,
        customer_name=crm.name,
        customer_email=crm.email,
        customer_tier=crm.tier,
        knowledge_sources=[a.title for a in articles],
        sentiment=sentiment_data.mood,
        churn_risk=sentiment_data.churn_risk_score,
        language=detected_lang,
        internal_notes=handoff_brief or "",
    )

    webhook_result = None
    if needs_human or decision.urgency_score >= 2.0 or sentiment_data.churn_risk_score >= 0.6:
        webhook_result = dispatch_slack_alert(
            ticket_id=ticket_id,
            customer_name=crm.name,
            customer_tier=crm.tier,
            department=decision.department,
            urgency_score=decision.urgency_score,
            rule_reason=rule_reason,
            sla_hours=sla_hours,
            sentiment=sentiment_data.mood,
        )

    return {
        "id": ticket_id,
        "ticket": safe_ticket,
        "guardrails": {
            "has_pii": pii_report.has_pii,
            "redacted_items": pii_report.redacted_items,
        },
        "customer": {
            "name": crm.name,
            "email": crm.email,
            "tier": crm.tier,
            "company": crm.company,
            "mrr": crm.monthly_recurring_revenue,
            "ltv": crm.lifetime_value,
            "renewal_days_left": crm.renewal_days_left,
            "account_manager": crm.account_manager,
            "health_status": crm.health_status,
        },
        "language": detected_lang,
        "sentiment": {
            "mood": sentiment_data.mood,
            "churn_risk_score": sentiment_data.churn_risk_score,
            "retention_playbook": sentiment_data.retention_playbook,
            "signals": sentiment_data.detected_signals,
            "predicted_csat": predicted_csat,
        },
        "jev": {
            "model": decision.model,
            "department": decision.department,
            "department_confidence": round(decision.department_confidence, 4),
            "urgency_score": round(decision.urgency_score, 4),
            "urgency_confidence": round(decision.urgency_confidence, 4),
            "refund_probability": round(decision.refund_probability, 4),
            "human_review_probability": round(decision.human_review_probability, 4),
            "is_simulated": decision.is_simulated,
        },
        "automation": {
            "route": route,
            "needs_human": needs_human,
            "reason": rule_reason,
            "sla_hours": sla_hours,
            "webhook_alert": webhook_result,
        },
        "knowledge_sources": [
            {"title": a.title, "category": a.category, "excerpt": a.content[:140] + "..."}
            for a in articles
        ],
        "suggested_reply": reply,
        "handoff_brief": handoff_brief,
    }


@app.post("/api/copilot/tune-tone")
def api_tune_tone(payload: ToneTuneRequest):
    """Rewrites a draft reply into Formal, Empathetic, or Concise tone via Groq LLM or deterministic fallback."""
    tuned = tune_response_tone(
        original_text=payload.text,
        tone_mode=payload.tone,
        customer_name=payload.customer_name,
    )
    return {"status": "ok", "tone": payload.tone, "tuned_reply": tuned}


@app.post("/api/webhooks/incoming")
def receive_incoming_webhook(payload: IncomingWebhookPayload):
    """Inbound webhook ingestion endpoint for external systems (Zendesk, Stripe, Intercom, Salesforce).
    Sanitizes PII, runs calibrated Jev triage, stores ticket, and triggers automated handoffs."""
    pii_report = sanitize_ticket_pii(payload.ticket_text)
    safe_ticket = pii_report.sanitized_text

    decision = analyze_ticket(safe_ticket)
    sentiment_data = analyze_sentiment(safe_ticket)
    detected_lang = detect_language(safe_ticket)
    crm = get_customer_crm_profile(payload.customer_name or payload.customer_email, payload.customer_tier)

    route, needs_human, rule_reason, sla_hours = choose_route(
        decision.department,
        decision.department_confidence,
        decision.urgency_score,
        decision.human_review_probability,
        customer_tier=payload.customer_tier,
        churn_risk=sentiment_data.churn_risk_score,
    )

    handoff_brief = None
    if needs_human or decision.urgency_score >= 1.8:
        handoff_obj = generate_specialist_handoff(
            ticket_id=0,
            customer_name=crm.name,
            customer_tier=crm.tier,
            ltv=crm.lifetime_value,
            department=decision.department,
            urgency_score=decision.urgency_score,
            churn_risk=sentiment_data.churn_risk_score,
            rule_reason=rule_reason,
        )
        handoff_brief = handoff_obj.briefing_markdown

    reply = f"Auto-triaged by ResolveIQ via inbound webhook ({payload.source}). Route: {route}."

    ticket_id = save_ticket(
        ticket_text=safe_ticket,
        department=decision.department,
        department_confidence=decision.department_confidence,
        urgency_score=decision.urgency_score,
        urgency_confidence=decision.urgency_confidence,
        refund_probability=decision.refund_probability,
        human_review_probability=decision.human_review_probability,
        route=route,
        needs_human=needs_human,
        rule_reason=rule_reason,
        sla_deadline_hours=sla_hours,
        suggested_reply=reply,
        customer_name=crm.name,
        customer_email=crm.email,
        customer_tier=crm.tier,
        sentiment=sentiment_data.mood,
        churn_risk=sentiment_data.churn_risk_score,
        language=detected_lang,
        internal_notes=handoff_brief or "",
    )

    return {
        "status": "ingested",
        "ticket_id": ticket_id,
        "source": payload.source,
        "department": decision.department,
        "urgency_score": round(decision.urgency_score, 2),
        "route": route,
        "needs_human": needs_human,
        "sla_hours": sla_hours,
        "handoff_brief": handoff_brief,
    }


@app.get("/api/roi")
def get_roi_metrics():
    """Calculates quantifiable time and cost savings compared to traditional human support."""
    summary = get_analytics_summary()
    total = summary.get("total_tickets", 0)
    escalated = summary.get("escalated_count", 0)
    roi = calculate_business_roi(total, escalated)
    return {
        "total_tickets": roi.total_tickets,
        "deflected_tickets": roi.deflected_tickets,
        "deflection_rate_pct": roi.deflection_rate_pct,
        "agent_hours_saved": roi.agent_hours_saved,
        "total_cost_saved_usd": roi.total_cost_saved_usd,
        "ai_compute_cost_usd": roi.ai_compute_cost_usd,
        "net_savings_usd": roi.net_savings_usd,
        "avg_speedup_factor": roi.avg_speedup_factor,
    }


@app.get("/api/benchmark")
def run_benchmark():
    """Runs automated accuracy and calibration evaluation against the golden test suite."""
    eval_res = run_model_benchmark()
    return {
        "total_eval_samples": eval_res.total_eval_samples,
        "department_accuracy_pct": eval_res.department_accuracy_pct,
        "urgency_mae": eval_res.urgency_mae,
        "safety_grounding_score": eval_res.safety_grounding_score,
        "detailed_metrics": eval_res.detailed_metrics,
    }


@app.post("/api/tickets/{ticket_id}/csat")
def submit_csat(ticket_id: int, payload: CSATRequest):
    """Submits customer satisfaction rating (1-5 stars). Low rating auto-escalates ticket."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    success = record_csat_feedback(ticket_id, rating=payload.rating, feedback=payload.feedback)
    return {
        "status": "recorded",
        "ticket_id": ticket_id,
        "rating": payload.rating,
        "escalated": payload.rating <= 2,
    }


@app.post("/api/transcribe")
async def transcribe_voice_ticket(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    transcription = transcribe_audio_file(audio_bytes, filename=file.filename or "voicemail.wav")
    return {"transcription": transcription}


@app.get("/api/engineering-spikes")
def engineering_incident_spikes():
    tickets = get_tickets(limit=100)
    spikes = detect_incident_spikes(tickets)
    return {
        "active_clusters": [
            {
                "topic": s.topic,
                "severity": s.severity,
                "affected_tickets_count": s.affected_tickets_count,
                "detected_pattern": s.detected_pattern,
                "sample_quotes": s.sample_quotes,
                "jira_issue": s.suggested_jira_issue,
            }
            for s in spikes
        ]
    }


@app.post("/api/tickets/{ticket_id}/send-email")
def send_resolution_email(ticket_id: int, payload: EmailDispatchRequest):
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    result = generate_branded_resolution_email(
        ticket_id=ticket_id,
        customer_name=ticket.get("customer_name") or "Customer",
        subject=payload.subject or f"[Resolved] Ticket #{ticket_id} Support Resolution",
        body_text=payload.body or ticket.get("final_reply") or ticket.get("suggested_reply") or "Your issue has been resolved.",
        sla_hours=ticket.get("sla_deadline_hours", 12),
        department=ticket.get("department", "general"),
    )

    record_action_taken(
        ticket_id,
        action_type="branded_email_dispatch",
        action_details={"recipient": result["recipient"], "subject": result["subject"]},
    )

    return result


@app.post("/api/tickets/{ticket_id}/action")
def execute_ticket_action(ticket_id: int, payload: ActionExecuteRequest):
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    email = ticket.get("customer_email") or f"{ticket.get('customer_name', 'user')}@example.com"

    if payload.action_type == "stripe_refund":
        result = execute_stripe_refund(ticket_id, customer_email=email, amount_usd=payload.amount, reason=payload.reason)
    elif payload.action_type == "auth0_reset":
        result = execute_auth0_password_reset(ticket_id, customer_email=email)
    elif payload.action_type == "session_unlock":
        result = execute_session_unlock(ticket_id, customer_email=email)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {payload.action_type}")

    record_action_taken(
        ticket_id,
        action_type=result.action_type,
        action_details={"message": result.message, "details": result.details, "action_id": result.action_id},
    )

    return {
        "status": "success",
        "action_id": result.action_id,
        "message": result.message,
        "details": result.details,
        "executed_at": result.executed_at,
    }


@app.get("/api/tickets/{ticket_id}/messages")
def get_thread_messages(ticket_id: int):
    return get_ticket_messages(ticket_id)


@app.post("/api/tickets/{ticket_id}/reply")
def post_followup_message(ticket_id: int, payload: FollowupMessageRequest):
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    msg_id = add_ticket_message(ticket_id, sender=payload.sender, message_text=payload.message)
    return {"status": "sent", "message_id": msg_id, "ticket_id": ticket_id}


@app.get("/api/tickets")
def list_tickets(status: str | None = None, limit: int = 50):
    return get_tickets(status=status, limit=limit)


@app.get("/api/tickets/{ticket_id}")
def get_single_ticket(ticket_id: int):
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket["thread"] = get_ticket_messages(ticket_id)
    return ticket


@app.patch("/api/tickets/{ticket_id}")
def update_ticket_endpoint(ticket_id: int, payload: TicketUpdateRequest):
    success = update_ticket(
        ticket_id,
        status=payload.status,
        final_reply=payload.final_reply,
        override_department=payload.override_department,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Ticket not found or no updates provided")
    return {"status": "updated", "id": ticket_id}


@app.get("/api/analytics")
def analytics():
    return get_analytics_summary()


@app.post("/api/batch-analyze")
def batch_analyze(payload: BatchRequest):
    results = []
    for item in payload.items:
        raw_text = item.ticket.strip()
        if len(raw_text) < 5:
            continue
        pii = sanitize_ticket_pii(raw_text)
        text = pii.sanitized_text

        decision = analyze_ticket(text)
        sentiment_data = analyze_sentiment(text)
        lang = detect_language(text)

        route, needs_human, reason, sla_hours = choose_route(
            decision.department,
            decision.department_confidence,
            decision.urgency_score,
            decision.human_review_probability,
            customer_tier=item.customer_tier,
            churn_risk=sentiment_data.churn_risk_score,
        )
        articles = search_knowledge_base(text, top_k=1)
        snippets = [f"{a.title}: {a.content}" for a in articles]

        try:
            reply = draft_reply(
                text, decision, route, customer_tier=item.customer_tier,
                knowledge_snippets=snippets, customer_language=lang,
                sentiment=sentiment_data.mood, retention_guidance=sentiment_data.retention_playbook,
            )
        except Exception:
            reply = f"Automated acknowledgment for {decision.department} issue. Route: {route}."

        tid = save_ticket(
            ticket_text=text,
            department=decision.department,
            department_confidence=decision.department_confidence,
            urgency_score=decision.urgency_score,
            urgency_confidence=decision.urgency_confidence,
            refund_probability=decision.refund_probability,
            human_review_probability=decision.human_review_probability,
            route=route,
            needs_human=needs_human,
            rule_reason=reason,
            sla_deadline_hours=sla_hours,
            suggested_reply=reply,
            customer_name=item.customer_name,
            customer_tier=item.customer_tier,
            knowledge_sources=[a.title for a in articles],
            sentiment=sentiment_data.mood,
            churn_risk=sentiment_data.churn_risk_score,
            language=lang,
        )

        results.append({
            "id": tid,
            "name": item.customer_name,
            "tier": item.customer_tier,
            "department": decision.department,
            "urgency": decision.urgency_score,
            "route": route,
            "needs_human": needs_human,
            "sla_hours": sla_hours,
            "sentiment": sentiment_data.mood,
        })

    return {"processed": len(results), "tickets": results}


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    items = []
    for row in reader:
        ticket_text = row.get("ticket") or row.get("description") or row.get("text") or ""
        if not ticket_text.strip():
            continue
        items.append(
            BatchItem(
                ticket=ticket_text.strip(),
                customer_name=row.get("customer_name") or row.get("name") or "CSV User",
                customer_tier=row.get("customer_tier") or row.get("tier") or "Pro",
            )
        )

    if not items:
        raise HTTPException(status_code=400, detail="No valid tickets found in CSV.")

    return batch_analyze(BatchRequest(items=items))


@app.get("/api/export-csv")
def export_csv():
    tickets = get_tickets(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Customer Name", "Tier", "Language", "Sentiment", "Department",
        "Dept Confidence", "Urgency (0-3)", "Refund Prob", "Human Review Prob",
        "Route", "Needs Human", "SLA Hours", "Status", "Created At", "Ticket Snippet"
    ])

    for t in tickets:
        writer.writerow([
            t["id"],
            t["customer_name"],
            t["customer_tier"],
            t.get("language", "English"),
            t.get("sentiment", "Calm"),
            t["department"],
            t["department_confidence"],
            t["urgency_score"],
            t["refund_probability"],
            t["human_review_probability"],
            t["route"],
            "Yes" if t["needs_human"] else "No",
            t["sla_deadline_hours"],
            t["status"],
            t["created_at"],
            t["ticket_text"][:80].replace("\n", " "),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=resolveiq_export.csv"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
