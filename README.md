# ⚡ ResolveIQ-by-Jev

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub: Tanish-o9](https://img.shields.io/badge/Author-Tanish--o9-181717.svg?logo=github)](https://github.com/Tanish-o9)
[![Python: 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI: Modern](https://img.shields.io/badge/FastAPI-2.2.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

> **Autonomous Customer Support Triage & Agent Hub combining TypeSafe AI (Jev) calibrated decisions, Customer 360 CRM enrichment, Speech-to-Text voicemails, Incident Spikes clustering with Jira generation, Branded HTML emails, and a public Self-Service Portal.**

---

## 🎯 Architecture & Design Philosophy

Traditional customer support systems fail because uncalibrated LLMs hallucinate policies, lack customer context, and cannot trigger real operations.

**ResolveIQ-by-Jev implements an end-to-end autonomous customer support architecture:**
```
[ Customer Input: Text, Audio/Voicemail, or Public Portal ]
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 1: Customer 360 CRM & Calibrated Decision         │
│  - Account enrichment: MRR, LTV, Renewal, Account Lead  │
│  - Calibrated department confidence via TypeSafe Jev    │
│  - 0-3 Urgency score rubric & Refund risk probability   │
│  - Multi-language detection (Hindi, Spanish, French...) │
│  - Sentiment analysis & Churn Threat Playbook           │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 2: Deterministic Business & SLA Routing           │
│  - Enterprise VIP routing & 1-hour critical SLA         │
│  - Instant Slack / Discord Webhook notification         │
│  - Active Incident Spike Clustering (Jira / GitHub)     │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 3: Grounded Multi-Lingual Draft (LangChain/Groq)  │
│  - RAG search in company policies & refund rules        │
│  - Native language response generation                  │
│  - Human-in-the-loop review, edit & department override │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Tier 4: Tool Actions & Multi-Channel Delivery          │
│  - Issue Stripe Refunds ($29 Pro duplicate charges)     │
│  - Dispatch Auth0 password reset & SSO tokens           │
│  - Dispatch Branded HTML Resolution Email to Customer   │
│  - Multi-turn conversation threading in SQLite          │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **🧠 TypeSafe Jev Calibrated Triage**: Calibrated department confidence, 0–3 urgency rubric, refund risk, and human review probability.
- **👤 Customer 360° CRM Profile**: Enriches every ticket with real-time account data (Company, MRR, Lifetime Value, Renewal countdown, Assigned Account Manager, and Health Status).
- **🎙️ Voice Note / Audio Voicemail Triage**: Built-in speech-to-text allowing customers or agents to speak tickets or upload voicemail recordings.
- **🚨 Incident Spikes & Jira Auto-Generator**: Clusters recurring customer bug reports in real time, assigns severity (`P1 Outage`, `P2 Degraded`), and formats ready-to-file Jira/GitHub issue markdown.
- **✉️ Branded HTML Email Dispatcher**: Renders and delivers responsive, branded HTML customer resolution emails with ticket tracking and SLA timestamps.
- **🌐 Public Customer Help Center (`/portal`)**: A clean self-service portal where customers can submit issues, receive instant AI policy resolutions, or request a human specialist.
- **⚡ Autonomous Tool Calling Actions**:
  - `Issue Stripe Refund`: Executes simulated Stripe refund with transaction ID and receipt URL.
  - `Send Auth0 Reset`: Dispatches one-time password reset links.
  - `Unlock Session`: Revokes stale tokens and issues corporate workspace re-invites.
- **😡 Sentiment & Churn Risk Meter**: Detects customer mood (`Calm`, `Frustrated`, `Angry`) and triggers retention courtesy discounts on cancellation threats.
- **🌐 Multi-Language Detection**: Supports Hindi/Hinglish, Spanish, French, German, and English.
- **🔔 Real-Time Webhook Alerting**: Dispatches instant rich alerts to `#support-urgent` in Slack or Discord.
- **💬 Threaded Conversations (Multi-turn Support)**: Multi-turn thread history where support agents and customers can post follow-up replies.
- **📊 SLA & Analytics Dashboard**: Real-time charts powered by Chart.js displaying department split, urgency distribution, and tier volume.
- **🐳 Docker & Docker Compose**: Production-ready containerization for 1-command deployment.

---

## 🚀 Quick Start

### 1. Run Locally
```bash
git clone https://github.com/Tanish-o9/ResolveIQ-by-Jev.git
cd ResolveIQ-by-Jev
pip install -r requirements.txt
python app.py
```
- Open **`http://localhost:8080`** for the Agent Console.
- Open **`http://localhost:8080/portal`** for the Customer Self-Service Portal.

### 2. Run with Docker Compose
```bash
docker compose up --build
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Triage ticket (Jev scores, CRM 360, sentiment, language, SLA, draft reply) |
| `POST` | `/api/transcribe` | Transcribe audio voicemail into ticket text |
| `GET` | `/api/engineering-spikes` | Detect incident spikes and get auto-generated Jira issue markdown |
| `POST` | `/api/tickets/{id}/send-email` | Generate and dispatch branded HTML resolution email |
| `POST` | `/api/tickets/{id}/action` | Execute tool action (`stripe_refund`, `auth0_reset`, `session_unlock`) |
| `GET` | `/api/tickets/{id}/messages` | Get full multi-turn conversation thread |
| `POST` | `/api/tickets/{id}/reply` | Add customer or agent follow-up reply |
| `GET` | `/api/tickets` | Query persistent tickets from SQLite |
| `PATCH` | `/api/tickets/{id}` | Update status (`resolved`, `escalated`) or override department |
| `GET` | `/api/analytics` | Aggregated SLA, department, and escalation metrics |
| `GET` | `/api/export-csv` | Download complete database tickets as CSV report |

---

## 🧪 Running Automated Tests

```bash
python tests/test_triage.py
```
> `Ran 10 tests in 0.046s — OK`

---

## 👨‍💻 Author & Contact

Developed & Maintained by **Tanish Rajput**
- 🐙 **GitHub:** [@Tanish-o9](https://github.com/Tanish-o9)
- 💼 **Project Repository:** [https://github.com/Tanish-o9/ResolveIQ-by-Jev](https://github.com/Tanish-o9/ResolveIQ-by-Jev)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
