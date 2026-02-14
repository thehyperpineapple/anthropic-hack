import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import anthropic
import httpx
import requests

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for structured order extraction via Claude (Skill 1)
# ---------------------------------------------------------------------------
ORDER_EXTRACTION_SYSTEM_PROMPT = """You are an order-data extraction assistant.
Given a transcript of a customer interaction (voice call, email, or PDF text),
extract every line item the customer wants to order.

Return ONLY a JSON array.  Each element must have exactly these keys:
  - "sku"   : string  — the product SKU mentioned by the customer
  - "qty"   : integer — the quantity requested
  - "color" : string  — the color or variant if mentioned, otherwise "default"

Example output:
[
  {"sku": "SKU-1234", "qty": 500, "color": "default"}
]

Do NOT include any explanation, markdown fences, or extra keys.
"""

WC_BASE_URL = "https://api.whitecircle.ai"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class TranscriptionError(Exception):
    """Raised when all transcription providers fail."""


class AIService:
    """Encapsulates all AI / external-model calls.

    Uses:
      - Anthropic Claude for structured order extraction (Skill 1)
      - White Circle for content moderation / safety verification (Skill 2)
      - ElevenLabs / OpenAI Whisper for audio transcription
    """

    def __init__(self) -> None:
        self.anthropic_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )

    # ------------------------------------------------------------------
    # Voice transcription  (ElevenLabs primary, OpenAI Whisper fallback)
    # ------------------------------------------------------------------
    async def transcribe_audio(self, file_url: str) -> str:
        """Transcribe an audio file to text.

        Primary path: ElevenLabs Speech-to-Text API (requires ELEVENLABS_API_KEY).
        Fallback path: OpenAI Whisper (requires OPENAI_API_KEY).

        file_url may be a local filesystem path OR an https:// URL.
        """
        local_path: str | None = None
        tmp_path: str | None = None

        try:
            # --- Resolve file_url to a local path ---
            if file_url.startswith(("https://", "http://")):
                logger.info("Downloading remote audio from %s", file_url)
                async with httpx.AsyncClient() as client:
                    resp = await client.get(file_url, follow_redirects=True, timeout=60.0)
                    resp.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(suffix=".audio", delete=False)
                tmp.write(resp.content)
                tmp.close()
                tmp_path = tmp.name
                local_path = tmp_path
            else:
                if not Path(file_url).is_file():
                    raise TranscriptionError(f"Local audio file not found: {file_url}")
                local_path = file_url

            # --- Primary: ElevenLabs ---
            elevenlabs_error: Exception | None = None
            if settings.ELEVENLABS_API_KEY:
                try:
                    return await self._transcribe_elevenlabs(local_path)
                except Exception as exc:
                    elevenlabs_error = exc
                    logger.error("ElevenLabs transcription failed: %s", exc)
            else:
                logger.warning("ELEVENLABS_API_KEY not set — skipping ElevenLabs")

            # --- Fallback: OpenAI Whisper ---
            openai_error: Exception | None = None
            if settings.OPENAI_API_KEY:
                try:
                    return await self._transcribe_whisper(local_path)
                except Exception as exc:
                    openai_error = exc
                    logger.error("OpenAI Whisper transcription failed: %s", exc)
            else:
                logger.warning("OPENAI_API_KEY not set — skipping Whisper fallback")

            # --- Both failed or both keys missing ---
            parts: list[str] = []
            if elevenlabs_error:
                parts.append(f"ElevenLabs: {elevenlabs_error}")
            if openai_error:
                parts.append(f"Whisper: {openai_error}")
            if not settings.ELEVENLABS_API_KEY and not settings.OPENAI_API_KEY:
                parts.append("No transcription API keys configured")
            raise TranscriptionError(
                f"All transcription providers failed for {file_url}. " + "; ".join(parts)
            )

        finally:
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    async def _transcribe_elevenlabs(self, local_path: str) -> str:
        """Call ElevenLabs Speech-to-Text API."""
        logger.info("Transcribing via ElevenLabs: %s", local_path)
        async with httpx.AsyncClient() as client:
            with open(local_path, "rb") as f:
                resp = await client.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": settings.ELEVENLABS_API_KEY},
                    files={"file": (Path(local_path).name, f)},
                    data={"model_id": "scribe_v1"},
                    timeout=120.0,
                )
            resp.raise_for_status()
        text = resp.json().get("text", "")
        if not text:
            raise TranscriptionError("ElevenLabs returned empty transcript")
        logger.info("ElevenLabs transcription complete (%d chars)", len(text))
        return text

    async def _transcribe_whisper(self, local_path: str) -> str:
        """Call OpenAI Whisper API as fallback."""
        logger.info("Transcribing via OpenAI Whisper: %s", local_path)
        import openai

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        with open(local_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        text = transcript.text
        if not text:
            raise TranscriptionError("Whisper returned empty transcript")
        logger.info("Whisper transcription complete (%d chars)", len(text))
        return text

    # ------------------------------------------------------------------
    # Structured extraction via Anthropic Claude  (Skill 1)
    # ------------------------------------------------------------------
    async def extract_order_data(self, text: str) -> list[dict[str, Any]]:
        """Send transcript text to Claude and get back structured order items."""
        logger.info("extract_order_data called — using Anthropic Claude")

        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            temperature=0,
            system=ORDER_EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )

        raw_text = response.content[0].text
        items: list[dict[str, Any]] = json.loads(raw_text)

        logger.info("Extracted %d line items via Claude", len(items))
        return items

    # ------------------------------------------------------------------
    # Content moderation via White Circle  (Skill 2)
    # ------------------------------------------------------------------
    async def verify_content_safety(
        self, text: str, context: str = "order_processing"
    ) -> dict[str, Any]:
        """Run a White Circle policy verification check on text.

        Returns the full API response dict with keys:
          decision  — "allow", "block", or "flag"
          actions   — list of recommended actions
          reason    — human-readable explanation
        """
        logger.info("verify_content_safety called — using White Circle")

        def _call() -> dict[str, Any]:
            resp = requests.post(
                f"{WC_BASE_URL}/policies/verify",
                headers={
                    "Authorization": f"Bearer {settings.WHITE_CIRCLE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "content": text,
                    "context": context,
                },
            )
            resp.raise_for_status()
            return resp.json()

        result = await asyncio.to_thread(_call)
        logger.info("White Circle decision: %s", result.get("decision"))
        return result
