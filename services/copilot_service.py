"""AI Copilot 1-Click Tone Tuner: Rewrites responses into Formal, Empathetic, or Concise styles."""
from __future__ import annotations

import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

TONE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert customer support copywriter. Rewrite the provided support response into the requested tone.\n"
            "Style Guidelines:\n"
            "- 'formal': Professional, structured, executive corporate language with formal sign-off.\n"
            "- 'empathetic': Warm, deeply apologetic, validating the customer's frustration, and reassuring.\n"
            "- 'concise': Extremely punchy, maximum 2-3 sentences or direct bullet points, under 50 words.\n"
            "Keep the underlying facts, policies, and non-committal boundaries identical.",
        ),
        (
            "human",
            "Target Tone: {tone}\nCustomer Name: {customer_name}\nOriginal Draft:\n{original_text}\n\nRewrite the response:",
        ),
    ]
)


def tune_response_tone(original_text: str, tone_mode: str, customer_name: str = "Customer") -> str:
    """Transforms a draft reply into Formal, Empathetic, or Concise tone."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if api_key and api_key != "your_groq_api_key":
        try:
            model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
            llm = ChatGroq(api_key=api_key, model=model, temperature=0.3)
            chain = TONE_PROMPT | llm | StrOutputParser()
            return chain.invoke({
                "tone": tone_mode,
                "customer_name": customer_name,
                "original_text": original_text,
            })
        except Exception:
            pass  # Fall back to heuristic tone rewrites

    # High-quality offline heuristic transformations
    if tone_mode == "formal":
        return (
            f"Dear {customer_name},\n\n"
            f"Thank you for contacting our support team. Regarding your inquiry:\n\n"
            f"{original_text}\n\n"
            f"Please be advised that your case is under review in accordance with our service level agreement. "
            f"Should you require further clarification, please do not hesitate to contact us.\n\n"
            f"Sincerely,\nResolveIQ Enterprise Support Operations"
        )
    elif tone_mode == "empathetic":
        return (
            f"Hi {customer_name},\n\n"
            f"I completely understand how frustrating and stressful this situation is, and I want to sincerely apologize for the inconvenience this has caused you.\n\n"
            f"{original_text}\n\n"
            f"We are treating this with top priority and are actively seeing this through until it is 100% resolved for you. Thank you so much for your patience with us!"
        )
    elif tone_mode == "concise":
        lines = [line.strip() for line in original_text.split(".") if len(line.strip()) > 5]
        bullets = "\n".join(f"• {l}." for l in lines[:2])
        return f"Hi {customer_name},\n\n{bullets}\n\nWe are actively handling this for you."

    return original_text
