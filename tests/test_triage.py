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
from services.db import (
    init_db,
    save_ticket,
    get_ticket,
    update_ticket,
    add_ticket_message,
    get_ticket_messages,
    record_action_taken,
    get_analytics_summary,
)


class TestResolveIQByJev(unittest.TestCase):
    def setUp(self):
        init_db()
        self.client = TestClient(app)

    def test_knowledge_base_search(self):
        results = search_knowledge_base("I was charged twice and want a refund", top_k=2)
        self.assertTrue(len(results) > 0)
        self.assertIn("Duplicate Charge", results[0].title)

    def test_sentiment_and_churn_analysis(self):
        angry_res = analyze_sentiment("I will cancel our company subscription! This is a horrible waste of money!")
        self.assertIn("Angry", angry_res.mood)
        self.assertGreater(angry_res.churn_risk_score, 0.6)
        self.assertIsNotNone(angry_res.retention_playbook)

        calm_res = analyze_sentiment("Thank you so much, please how do I change my profile photo?")
        self.assertEqual(calm_res.mood, "Calm")
        self.assertLess(calm_res.churn_risk_score, 0.3)

    def test_language_detection(self):
        self.assertEqual(detect_language("Hello, I need help with my invoice"), "English")
        self.assertEqual(detect_language("Mujhe refund chahiye kripya madad karo"), "Hindi / Hinglish")
        self.assertEqual(detect_language("Hola por favor necesito ayuda con mi cuenta"), "Spanish")

    def test_crm_360_profile_enrichment(self):
        profile = get_customer_crm_profile("Sarah Jenkins", "Pro")
        self.assertEqual(profile.name, "Sarah Jenkins")
        self.assertGreater(profile.lifetime_value, 1000)
        self.assertEqual(profile.tier, "Pro")

    def test_audio_voicemail_transcription(self):
        transcription = transcribe_audio_file(b"RIFFdummydataWAVE", filename="test.wav")
        self.assertTrue(len(transcription) > 10)
        self.assertIn("voicemail", transcription.lower())

    def test_incident_spike_clustering(self):
        tickets = [
            {"ticket_text": "CSV export keeps hanging on large report"},
            {"ticket_text": "My CSV download is failing repeatedly"},
        ]
        spikes = detect_incident_spikes(tickets)
        self.assertTrue(len(spikes) >= 1)
        self.assertIn("CSV", spikes[0].topic)
        self.assertIn("title", spikes[0].suggested_jira_issue)

    def test_branded_email_generation(self):
        email = generate_branded_resolution_email(
            ticket_id=101,
            customer_name="Sarah",
            subject="Resolution update",
            body_text="Your duplicate refund was processed.",
            sla_hours=2,
            department="billing",
        )
        self.assertEqual(email["status"], "delivered")
        self.assertIn("<html", email["html"])
        self.assertIn("ResolveIQ", email["html"])

    def test_tool_calling_actions(self):
        refund = execute_stripe_refund(ticket_id=99, customer_email="user@test.com", amount_usd=49.00)
        self.assertTrue(refund.success)
        self.assertTrue(refund.action_id.startswith("re_"))
        self.assertEqual(refund.details["amount_refunded"], "$49.00")

    def test_portal_route(self):
        resp = self.client.get("/portal")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Help Center", resp.text)

    def test_api_single_analyze_with_crm(self):
        payload = {
            "ticket": "I was charged twice on my invoice. Need a refund ASAP or I will cancel!",
            "customer_name": "Sarah Jenkins",
            "customer_tier": "Pro",
        }
        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("customer", data)
        self.assertEqual(data["customer"]["name"], "Sarah Jenkins")
        self.assertIn("mrr", data["customer"])
        self.assertIn("sentiment", data)
        self.assertIn("language", data)


if __name__ == "__main__":
    unittest.main()
