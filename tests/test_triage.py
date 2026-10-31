"""Comprehensive unit and integration test suite for ResolveIQ-by-Jev."""
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["TYPESAFE_API_KEY"] = ""  # Force demo mode for tests
os.environ["GROQ_API_KEY"] = ""

from fastapi.testclient import TestClient

from app import app, choose_route
from services.knowledge_service import search_knowledge_base
from services.sentiment_service import analyze_sentiment
from services.language_service import detect_language
from services.action_service import execute_stripe_refund, execute_auth0_password_reset
from services.webhook_service import dispatch_slack_alert
from services.crm_service import get_customer_crm_profile
from services.audio_service import transcribe_audio_file
from services.cluster_service import detect_incident_spikes
from services.email_service import generate_branded_resolution_email
from services.guardrails_service import sanitize_ticket_pii
from services.roi_service import calculate_business_roi
from services.csat_service import predict_csat_score
from services.eval_service import run_model_benchmark
from services.copilot_service import tune_response_tone
from services.handoff_service import generate_specialist_handoff
from services.db import (
    init_db,
    save_ticket,
    get_ticket,
    update_ticket,
    add_ticket_message,
    get_ticket_messages,
    record_action_taken,
    record_csat_feedback,
    get_analytics_summary,
)


class TestResolveIQByJev(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)

    def test_pii_sanitization_guardrails(self):
        raw = "My card is 4111-2222-3333-4444 and my API token is sk_live_abcdef1234567890123456. My password: supersecret123"
        report = sanitize_ticket_pii(raw)
        self.assertTrue(report.has_pii)
        self.assertNotIn("4111-2222-3333-4444", report.sanitized_text)
        self.assertNotIn("sk_live_", report.sanitized_text)
        self.assertIn("[REDACTED_CARD", report.sanitized_text)
        self.assertIn("[REDACTED_API_SECRET]", report.sanitized_text)
        self.assertIn("[REDACTED_PASSWORD]", report.sanitized_text)

    def test_business_roi_calculator(self):
        roi = calculate_business_roi(total_tickets=100, escalated_count=20)
        self.assertEqual(roi.total_tickets, 100)
        self.assertEqual(roi.deflected_tickets, 80)
        self.assertEqual(roi.deflection_rate_pct, 80.0)
        self.assertGreater(roi.agent_hours_saved, 10.0)
        self.assertGreater(roi.net_savings_usd, 100.0)

    def test_csat_prediction_and_recording(self):
        score_angry = predict_csat_score(urgency_score=2.8, sentiment_mood="Angry (High Churn Risk)", needs_human=True)
        self.assertEqual(score_angry, 2)

        score_calm = predict_csat_score(urgency_score=0.4, sentiment_mood="Calm", needs_human=False)
        self.assertEqual(score_calm, 5)

        # Save ticket and submit CSAT
        tid = save_ticket(
            ticket_text="Checking CSAT update",
            department="general",
            department_confidence=0.9,
            urgency_score=1.0,
            urgency_confidence=0.9,
            refund_probability=0.1,
            human_review_probability=0.1,
            route="General queue",
            needs_human=False,
            rule_reason="Safe",
            sla_deadline_hours=12,
            suggested_reply="Resolved draft",
            customer_name="CSAT Tester",
        )
        record_csat_feedback(tid, rating=5, feedback="Great service!")
        ticket = get_ticket(tid)
        self.assertEqual(ticket["csat_rating"], 5)

    def test_model_benchmark_runner(self):
        bench = run_model_benchmark()
        self.assertGreater(bench.total_eval_samples, 4)
        self.assertGreaterEqual(bench.department_accuracy_pct, 80.0)
        self.assertGreaterEqual(bench.safety_grounding_score, 90.0)

    def test_knowledge_base_search(self):
        results = search_knowledge_base("I was charged twice and want a refund", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertIn("Duplicate Charge", results[0].title)

    def test_sentiment_and_churn_analysis(self):
        angry_res = analyze_sentiment("I will cancel our company subscription! This is a horrible waste of money!")
        self.assertIn("Angry", angry_res.mood)
        self.assertGreater(angry_res.churn_risk_score, 0.6)
        self.assertIsNotNone(angry_res.retention_playbook)

    def test_language_detection(self):
        self.assertEqual(detect_language("Hello, I need help with my invoice"), "English")
        self.assertEqual(detect_language("Mujhe refund chahiye kripya madad karo"), "Hindi / Hinglish")
        self.assertEqual(detect_language("Hola por favor necesito ayuda con mi cuenta"), "Spanish")

    def test_crm_360_profile_enrichment(self):
        profile = get_customer_crm_profile("Sarah Jenkins", "Pro")
        self.assertEqual(profile.name, "Sarah Jenkins")
        self.assertGreater(profile.lifetime_value, 1000)

    def test_audio_voicemail_transcription(self):
        transcription = transcribe_audio_file(b"RIFFdummydataWAVE", filename="test.wav")
        self.assertTrue(len(transcription) > 10)

    def test_incident_spike_clustering(self):
        tickets = [
            {"ticket_text": "CSV export keeps hanging on large report"},
            {"ticket_text": "My CSV download is failing repeatedly"},
        ]
        spikes = detect_incident_spikes(tickets)
        self.assertTrue(len(spikes) >= 1)

    def test_tool_calling_actions(self):
        refund = execute_stripe_refund(ticket_id=99, customer_email="user@test.com", amount_usd=49.00)
        self.assertTrue(refund.success)
        self.assertTrue(refund.action_id.startswith("re_"))

    def test_portal_route(self):
        resp = self.client.get("/portal")
        self.assertEqual(resp.status_code, 200)

    def test_api_roi_endpoint(self):
        resp = self.client.get("/api/roi")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("deflection_rate_pct", data)
        self.assertIn("net_savings_usd", data)

    def test_api_benchmark_endpoint(self):
        resp = self.client.get("/api/benchmark")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("department_accuracy_pct", data)

    def test_api_single_analyze_with_guardrails(self):
        payload = {
            "ticket": "My credit card 4242-4242-4242-4242 was charged twice. Password: mysecretpass",
            "customer_name": "Sarah Jenkins",
            "customer_tier": "Pro",
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["guardrails"]["has_pii"])
        self.assertNotIn("4242-4242-4242-4242", data["ticket"])
        self.assertIn("customer", data)
        self.assertIn("predicted_csat", data["sentiment"])

    def test_copilot_tone_tuner(self):
        original = "We received your request. We cannot refund after 30 days."
        formal = tune_response_tone(original, "formal", "Alice")
        self.assertIn("Dear Alice", formal)
        empathetic = tune_response_tone(original, "empathetic", "Alice")
        self.assertIn("Alice", empathetic)
        concise = tune_response_tone(original, "concise", "Alice")
        self.assertTrue(len(concise.split()) < 40)

    def test_specialist_handoff(self):
        handoff = generate_specialist_handoff(
            ticket_id=42,
            customer_name="Globex Corp",
            customer_tier="Enterprise",
            ltv=12000.0,
            department="billing",
            urgency_score=2.8,
            churn_risk=0.8,
            rule_reason="Enterprise critical billing dispute",
        )
        self.assertIn("CONFIDENTIAL", handoff.briefing_markdown)
        self.assertIn("Senior Billing Operations", handoff.target_specialist_team)
        self.assertIn("CRITICAL", handoff.priority_level)

    def test_copilot_endpoint(self):
        resp = self.client.post(
            "/api/copilot/tune-tone",
            json={"text": "Please check your credentials and try again.", "tone": "concise", "customer_name": "Bob"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["tone"], "concise")
        self.assertIn("tuned_reply", data)

    def test_incoming_webhook_endpoint(self):
        resp = self.client.post(
            "/api/webhooks/incoming",
            json={
                "source": "zendesk",
                "ticket_text": "Production API database is throwing 500 errors across all endpoints!",
                "customer_name": "Dev Ops Lead",
                "customer_tier": "Enterprise",
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ingested")
        self.assertTrue(data["ticket_id"] > 0)
        self.assertIn("handoff_brief", data)


if __name__ == "__main__":
    unittest.main()
