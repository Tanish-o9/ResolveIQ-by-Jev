"""Optional LangChain + Groq generation layer.

Jev makes the structured decision. The LLM is only used to draft natural
language after the decision is made, grounded in company policy, detected language,
and customer sentiment de-escalation guidelines.
"""
from __future__ import annotations

import os
from typing import Iterator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from services.jev_service import JevDecision


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful, empathetic SaaS customer-support assistant.\n"
            "Guidelines:\n"
            "- Strictly adhere to the provided Company Knowledge & Policy context.\n"
            "- If the customer is Frustrated or High Churn Risk, adopt an apologetic, high-priority tone.\n"
            "- Follow the Retention Guidance if provided.\n"
            "- Do not make unverified financial promises.\n"
            "- Keep the response under 120 words.\n"
            "- If routed to a human specialist, inform the customer their ticket is being actively escalated.\n"
            "- LANGUAGE REQUIREMENT: Write the reply in {customer_language}.",
        ),
        (
            "human",
            "Customer ticket:\n{ticket}\n\n"
            "Customer tier: {customer_tier}\n"
            "Detected Sentiment: {sentiment}\n"
            "Retention Guidance: {retention_guidance}\n\n"
            "Jev triage decision:\n"
            "- Department: {department}\n"
            "- Department confidence: {department_confidence:.2f}\n"
            "- Urgency score: {urgency_score:.2f} on a 0-3 rubric\n"
            "- Refund-related probability: {refund_probability:.2f}\n"
            "- Human-review probability: {human_review_probability:.2f}\n"
            "- Final route: {route}\n\n"
            "Company Knowledge & Policy Context:\n{knowledge_context}\n\n"
            "Draft the suggested customer response in {customer_language}.",
        ),
    ]
)


def _get_llm() -> ChatGroq | None:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key":
        return None

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
    return ChatGroq(
        api_key=api_key,
        model=model,
        temperature=0.2,
        max_retries=2,
    )


def draft_reply(
    ticket: str,
    decision: JevDecision,
    route: str,
    customer_tier: str = "Pro",
    knowledge_snippets: list[str] | None = None,
    customer_language: str = "English",
    sentiment: str = "Calm",
    retention_guidance: str | None = None,
) -> str:
    llm = _get_llm()
    if not llm:
        prefix = f"[{customer_language}] " if customer_language != "English" else ""
        return (
            f"{prefix}Jev analysis completed. Optional LangChain reply generation is disabled "
            "because GROQ_API_KEY is not configured. Add your Groq key to .env to enable instant AI draft replies."
        )

    knowledge_context = (
        "\n".join(f"- {s}" for s in knowledge_snippets)
        if knowledge_snippets
        else "Standard customer support courtesy and company SLA policy."
    )

    chain = PROMPT | llm | StrOutputParser()

    return chain.invoke(
        {
            "ticket": ticket,
            "customer_tier": customer_tier,
            "department": decision.department,
            "department_confidence": decision.department_confidence,
            "urgency_score": decision.urgency_score,
            "refund_probability": decision.refund_probability,
            "human_review_probability": decision.human_review_probability,
            "route": route,
            "knowledge_context": knowledge_context,
            "customer_language": customer_language,
            "sentiment": sentiment,
            "retention_guidance": retention_guidance or "None",
        }
    )


def stream_draft_reply(
    ticket: str,
    decision: JevDecision,
    route: str,
    customer_tier: str = "Pro",
    knowledge_snippets: list[str] | None = None,
    customer_language: str = "English",
    sentiment: str = "Calm",
    retention_guidance: str | None = None,
) -> Iterator[str]:
    """Streams the reply token-by-token for live UX responsiveness."""
    llm = _get_llm()
    if not llm:
        yield f"[{customer_language}] Jev analysis completed. (GROQ_API_KEY is not configured)."
        return

    knowledge_context = (
        "\n".join(f"- {s}" for s in knowledge_snippets)
        if knowledge_snippets
        else "Standard customer support courtesy and company SLA policy."
    )

    chain = PROMPT | llm | StrOutputParser()
    for chunk in chain.stream(
        {
            "ticket": ticket,
            "customer_tier": customer_tier,
            "department": decision.department,
            "department_confidence": decision.department_confidence,
            "urgency_score": decision.urgency_score,
            "refund_probability": decision.refund_probability,
            "human_review_probability": decision.human_review_probability,
            "route": route,
            "knowledge_context": knowledge_context,
            "customer_language": customer_language,
            "sentiment": sentiment,
            "retention_guidance": retention_guidance or "None",
        }
    ):
        yield chunk
