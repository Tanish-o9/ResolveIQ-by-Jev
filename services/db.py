"""SQLite persistence layer for support tickets, triage decisions, threaded conversations, and audit trails."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "triage.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the SQLite database schema if not already present."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_text TEXT NOT NULL,
                customer_name TEXT DEFAULT 'Anonymous',
                customer_email TEXT DEFAULT '',
                customer_tier TEXT DEFAULT 'Pro',
                department TEXT NOT NULL,
                department_confidence REAL NOT NULL,
                urgency_score REAL NOT NULL,
                urgency_confidence REAL NOT NULL,
                refund_probability REAL NOT NULL,
                human_review_probability REAL NOT NULL,
                route TEXT NOT NULL,
                needs_human INTEGER NOT NULL,
                rule_reason TEXT NOT NULL,
                sla_deadline_hours INTEGER NOT NULL DEFAULT 12,
                suggested_reply TEXT NOT NULL,
                final_reply TEXT DEFAULT '',
                knowledge_sources TEXT DEFAULT '[]',
                sentiment TEXT DEFAULT 'Calm',
                churn_risk REAL DEFAULT 0.1,
                language TEXT DEFAULT 'English',
                actions_taken TEXT DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'triaged',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL
            );
            """
        )
        # Threaded messages table for conversation history
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                message_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );
            """
        )
        # Automatic schema migration for existing databases
        cursor = conn.execute("PRAGMA table_info(tickets)")
        columns = [row[1] for row in cursor.fetchall()]
        if "sentiment" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN sentiment TEXT DEFAULT 'Calm'")
        if "churn_risk" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN churn_risk REAL DEFAULT 0.1")
        if "language" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN language TEXT DEFAULT 'English'")
        if "actions_taken" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN actions_taken TEXT DEFAULT '[]'")
        conn.commit()


def save_ticket(
    ticket_text: str,
    department: str,
    department_confidence: float,
    urgency_score: float,
    urgency_confidence: float,
    refund_probability: float,
    human_review_probability: float,
    route: str,
    needs_human: bool,
    rule_reason: str,
    sla_deadline_hours: int,
    suggested_reply: str,
    customer_name: str = "Anonymous",
    customer_email: str = "",
    customer_tier: str = "Pro",
    knowledge_sources: list[str] | None = None,
    sentiment: str = "Calm",
    churn_risk: float = 0.1,
    language: str = "English",
) -> int:
    """Saves a triaged ticket and returns the new ticket ID."""
    init_db()
    sources_json = json.dumps(knowledge_sources or [])
    initial_status = "escalated" if needs_human else "triaged"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tickets (
                ticket_text, customer_name, customer_email, customer_tier,
                department, department_confidence, urgency_score, urgency_confidence,
                refund_probability, human_review_probability, route, needs_human,
                rule_reason, sla_deadline_hours, suggested_reply, final_reply,
                knowledge_sources, sentiment, churn_risk, language, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_text,
                customer_name,
                customer_email,
                customer_tier,
                department,
                department_confidence,
                urgency_score,
                urgency_confidence,
                refund_probability,
                human_review_probability,
                route,
                1 if needs_human else 0,
                rule_reason,
                sla_deadline_hours,
                suggested_reply,
                suggested_reply,
                sources_json,
                sentiment,
                churn_risk,
                language,
                initial_status,
            ),
        )
        ticket_id = cursor.lastrowid or 0

        # Save initial customer ticket as first message in thread
        cursor.execute(
            "INSERT INTO ticket_messages (ticket_id, sender, message_text) VALUES (?, ?, ?)",
            (ticket_id, "customer", ticket_text),
        )
        conn.commit()
        return ticket_id


def add_ticket_message(ticket_id: int, sender: str, message_text: str) -> int:
    """Adds a message to the conversation thread (from agent or customer)."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ticket_messages (ticket_id, sender, message_text) VALUES (?, ?, ?)",
            (ticket_id, sender, message_text),
        )
        conn.commit()
        return cursor.lastrowid or 0


def get_ticket_messages(ticket_id: int) -> list[dict[str, Any]]:
    """Gets all threaded messages for a ticket ordered chronologically."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY id ASC",
            (ticket_id,),
        )
        return [dict(r) for r in cursor.fetchall()]


def record_action_taken(ticket_id: int, action_type: str, action_details: dict[str, Any]) -> bool:
    """Appends an executed action (e.g., Stripe refund, Auth0 reset) to the ticket's action history."""
    init_db()
    ticket = get_ticket(ticket_id)
    if not ticket:
        return False

    actions = ticket.get("actions_taken") or []
    actions.append({
        "action_type": action_type,
        "details": action_details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    with get_connection() as conn:
        conn.execute(
            "UPDATE tickets SET actions_taken = ? WHERE id = ?",
            (json.dumps(actions), ticket_id),
        )
        # Also record system note in conversation thread
        conn.execute(
            "INSERT INTO ticket_messages (ticket_id, sender, message_text) VALUES (?, ?, ?)",
            (ticket_id, "system", f"Executed {action_type}: {action_details.get('message', 'Completed')}"),
        )
        conn.commit()
        return True


def get_tickets(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve tickets ordered by newest first, optionally filtered by status."""
    init_db()
    with get_connection() as conn:
        if status and status != "all":
            cursor = conn.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM tickets ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        rows = cursor.fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["needs_human"] = bool(d["needs_human"])
        try:
            d["knowledge_sources"] = json.loads(d.get("knowledge_sources") or "[]")
        except Exception:
            d["knowledge_sources"] = []
        try:
            d["actions_taken"] = json.loads(d.get("actions_taken") or "[]")
        except Exception:
            d["actions_taken"] = []
        result.append(d)
    return result


def get_ticket(ticket_id: int) -> dict[str, Any] | None:
    """Get a single ticket by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["needs_human"] = bool(d["needs_human"])
        try:
            d["knowledge_sources"] = json.loads(d.get("knowledge_sources") or "[]")
        except Exception:
            d["knowledge_sources"] = []
        try:
            d["actions_taken"] = json.loads(d.get("actions_taken") or "[]")
        except Exception:
            d["actions_taken"] = []
        return d


def update_ticket(
    ticket_id: int,
    status: str | None = None,
    final_reply: str | None = None,
    override_department: str | None = None,
) -> bool:
    """Updates status, final reply, or overrides the department."""
    init_db()
    updates = []
    params: list[Any] = []

    if status:
        updates.append("status = ?")
        params.append(status)
        if status == "resolved":
            updates.append("resolved_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

    if final_reply is not None:
        updates.append("final_reply = ?")
        params.append(final_reply)

    if override_department:
        updates.append("department = ?")
        params.append(override_department)

    if not updates:
        return False

    params.append(ticket_id)
    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        if status == "resolved" and final_reply:
            conn.execute(
                "INSERT INTO ticket_messages (ticket_id, sender, message_text) VALUES (?, ?, ?)",
                (ticket_id, "agent", final_reply),
            )
        conn.commit()
        return cursor.rowcount > 0


def get_analytics_summary() -> dict[str, Any]:
    """Computes aggregated support triage metrics for the dashboard."""
    init_db()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if total == 0:
            return {
                "total_tickets": 0,
                "escalated_count": 0,
                "escalation_rate": 0.0,
                "resolved_count": 0,
                "avg_urgency": 0.0,
                "avg_department_confidence": 0.0,
                "department_counts": {"billing": 0, "technical": 0, "account": 0, "general": 0},
                "urgency_buckets": {"Low (0-1)": 0, "Medium (1-2)": 0, "High/Critical (2-3)": 0},
                "tier_counts": {"Free": 0, "Pro": 0, "Enterprise": 0},
                "sentiment_counts": {"Calm": 0, "Frustrated": 0, "Angry (High Churn Risk)": 0},
            }

        escalated = conn.execute("SELECT COUNT(*) FROM tickets WHERE needs_human = 1").fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status = 'resolved'").fetchone()[0]
        avg_urgency = conn.execute("SELECT AVG(urgency_score) FROM tickets").fetchone()[0] or 0.0
        avg_conf = conn.execute("SELECT AVG(department_confidence) FROM tickets").fetchone()[0] or 0.0

        dept_rows = conn.execute("SELECT department, COUNT(*) FROM tickets GROUP BY department").fetchall()
        dept_counts = {"billing": 0, "technical": 0, "account": 0, "general": 0}
        for d, c in dept_rows:
            dept_counts[str(d).lower()] = c

        low_urg = conn.execute("SELECT COUNT(*) FROM tickets WHERE urgency_score < 1.0").fetchone()[0]
        med_urg = conn.execute("SELECT COUNT(*) FROM tickets WHERE urgency_score >= 1.0 AND urgency_score < 2.0").fetchone()[0]
        high_urg = conn.execute("SELECT COUNT(*) FROM tickets WHERE urgency_score >= 2.0").fetchone()[0]

        tier_rows = conn.execute("SELECT customer_tier, COUNT(*) FROM tickets GROUP BY customer_tier").fetchall()
        tier_counts = {"Free": 0, "Pro": 0, "Enterprise": 0}
        for t, c in tier_rows:
            tier_counts[str(t)] = c

        # Sentiment breakdown
        sent_rows = conn.execute("SELECT sentiment, COUNT(*) FROM tickets GROUP BY sentiment").fetchall()
        sentiment_counts = {"Calm": 0, "Frustrated": 0, "Angry (High Churn Risk)": 0}
        for s, c in sent_rows:
            if str(s) in sentiment_counts:
                sentiment_counts[str(s)] = c

    return {
        "total_tickets": total,
        "escalated_count": escalated,
        "escalation_rate": round((escalated / total) * 100, 1),
        "resolved_count": resolved,
        "avg_urgency": round(avg_urgency, 2),
        "avg_department_confidence": round(avg_conf * 100, 1),
        "department_counts": dept_counts,
        "urgency_buckets": {
            "Low (0-1)": low_urg,
            "Medium (1-2)": med_urg,
            "High/Critical (2-3)": high_urg,
        },
        "tier_counts": tier_counts,
        "sentiment_counts": sentiment_counts,
    }
