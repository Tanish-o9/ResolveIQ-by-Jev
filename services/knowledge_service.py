"""Knowledge base grounding and policy retrieval for customer support triage."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class KnowledgeArticle:
    title: str
    category: str
    content: str
    keywords: list[str]


KNOWLEDGE_BASE: list[KnowledgeArticle] = [
    KnowledgeArticle(
        title="Duplicate Charge & Refund Policy",
        category="billing",
        content=(
            "Duplicate billing occurrences are fully eligible for instant refund review. "
            "Refunds are processed back to the original payment method within 3 to 5 business days. "
            "Our billing team will need the transaction ID or invoice number to expedite the reversal."
        ),
        keywords=["charged twice", "duplicate", "refund", "invoice", "overcharge", "card", "money back"],
    ),
    KnowledgeArticle(
        title="Subscription Cancellation & Pro-rata Credits",
        category="billing",
        content=(
            "Customers may cancel anytime from Settings > Billing. "
            "We offer a 30-day money-back guarantee for first-time annual subscriptions. "
            "Mid-month cancellations retain access until the end of the billing cycle without automatic refunds."
        ),
        keywords=["cancel", "cancellation", "subscription", "annual", "prorated", "credit", "downgrade"],
    ),
    KnowledgeArticle(
        title="CSV & Data Export Troubleshooting",
        category="technical",
        content=(
            "If CSV export hangs or fails, verify that the date range filter does not exceed 100,000 rows. "
            "As an immediate workaround, trigger an asynchronous background export via Settings > Data Export "
            "or use the REST API `/v1/reports/export` endpoint."
        ),
        keywords=["csv", "export", "download", "data", "report", "hangs", "failed", "dashboard"],
    ),
    KnowledgeArticle(
        title="Workspace Access & Identity Changes",
        category="account",
        content=(
            "When an administrator changes a user's corporate email, the account session is invalidated. "
            "The user must accept the re-invitation email sent to their new address or contact their team admin "
            "to confirm Single Sign-On (SSO) claim mappings in Settings > Team Members."
        ),
        keywords=["access", "workspace", "email", "admin", "login", "sso", "restore", "permission", "member"],
    ),
    KnowledgeArticle(
        title="API Rate Limits & Server 429 Errors",
        category="technical",
        content=(
            "Standard accounts have a limit of 100 requests/minute. Enterprise accounts have up to 2,000 requests/minute. "
            "Check the `X-RateLimit-Reset` HTTP header. For quota increases, contact Enterprise support."
        ),
        keywords=["rate limit", "429", "api", "quota", "requests", "timeout", "slow", "integration"],
    ),
    KnowledgeArticle(
        title="Enterprise SLA & Dedicated Support",
        category="general",
        content=(
            "Enterprise tier customers are covered by a 1-hour critical response SLA and dedicated solution engineers. "
            "Tickets flagged as urgent are directly routed to the on-call specialist rotation."
        ),
        keywords=["enterprise", "sla", "critical", "vip", "priority", "on-call", "escalation"],
    ),
]


def search_knowledge_base(query: str, top_k: int = 2) -> list[KnowledgeArticle]:
    """Retrieves relevant knowledge articles based on keyword and token matching."""
    normalized = query.lower()
    scored_articles: list[tuple[float, KnowledgeArticle]] = []

    tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", normalized))

    for article in KNOWLEDGE_BASE:
        score = 0.0

        # Exact keyword match
        for kw in article.keywords:
            if kw.lower() in normalized:
                score += 3.0

        # Token overlap with article title and content
        title_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", article.title.lower()))
        content_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", article.content.lower()))

        score += len(tokens & title_tokens) * 2.0
        score += len(tokens & content_tokens) * 0.5

        if score > 0.0:
            scored_articles.append((score, article))

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [art for _, art in scored_articles[:top_k]]

