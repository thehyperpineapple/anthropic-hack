import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt that would be sent to Claude / any LLM for order extraction.
# Kept as a module-level constant so it can be reused or overridden in tests.
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


class AIService:
    """Encapsulates all AI / external-model calls.

    Methods are currently mocked with short delays to simulate real latency.
    Swap the bodies for actual SDK calls (Anthropic, ElevenLabs, etc.) when
    the keys are available.
    """

    # ------------------------------------------------------------------
    # Voice transcription  (simulates ElevenLabs / Whisper)
    # ------------------------------------------------------------------
    async def transcribe_audio(self, file_url: str) -> str:
        logger.info("transcribe_audio called for %s — using mock", file_url)
        await asyncio.sleep(0.3)  # simulate network latency
        return "I need 500 units of SKU-1234 and 20 units of SKU-5678 in blue"

    # ------------------------------------------------------------------
    # Structured extraction  (simulates Anthropic Claude call)
    # ------------------------------------------------------------------
    async def extract_order_data(self, text: str) -> list[dict[str, Any]]:
        logger.info("extract_order_data called — using mock")
        await asyncio.sleep(0.2)  # simulate LLM latency

        # Mock response matching the transcript produced by transcribe_audio
        mock_response: list[dict[str, Any]] = [
            {"sku": "SKU-1234", "qty": 500, "color": "default"},
            {"sku": "SKU-5678", "qty": 20, "color": "blue"},
        ]

        # In production this would be:
        # response = await anthropic_client.messages.create(
        #     model="claude-sonnet-4-5-20250929",
        #     system=ORDER_EXTRACTION_SYSTEM_PROMPT,
        #     messages=[{"role": "user", "content": text}],
        #     max_tokens=1024,
        # )
        # mock_response = json.loads(response.content[0].text)

        logger.info("Extracted %d line items", len(mock_response))
        return mock_response
