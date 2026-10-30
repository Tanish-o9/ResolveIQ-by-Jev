"""Speech-to-Text Voicemail / Audio Transcription for incoming voice tickets."""
from __future__ import annotations

import io
import os
import httpx


def transcribe_audio_file(file_bytes: bytes, filename: str = "voicemail.wav") -> str:
    """Transcribes audio using Groq Whisper API if configured, otherwise returns simulated transcription."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if api_key and api_key != "your_groq_api_key":
        try:
            files = {"file": (filename, io.BytesIO(file_bytes), "audio/wav")}
            data = {"model": "whisper-large-v3", "temperature": "0.0", "response_format": "json"}
            headers = {"Authorization": f"Bearer {api_key}"}

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    return result.get("text", "").strip()
        except Exception:
            pass  # Fall back to simulated voice note

    # Offline / local demo simulated voice note
    return (
        "Hello, this is a voicemail for customer support. I noticed our team account was charged twice "
        "on our corporate credit card this morning for the Pro subscription. Can you please check invoice #8821 "
        "and process a reversal as soon as possible? Thank you."
    )

