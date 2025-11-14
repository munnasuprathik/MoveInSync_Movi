"""
Vision helper utilities for Movi's LangGraph agent.

Processes dashboard screenshots via Anthropic's vision-capable models to extract
the trip or action the user highlighted, so the agent can automatically trigger
the correct flow.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from anthropic import Anthropic
from anthropic.types import Message

logger = logging.getLogger(__name__)

VISION_DEFAULTS = [
    "claude-sonnet-4-5-20250929",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-latest",
    "claude-3-sonnet-20240229",
]

_anthropic_client: Optional[Anthropic] = None


class VisionProcessingError(Exception):
    """Raised when a screenshot cannot be processed."""


@dataclass
class VisionExtraction:
    trip_name: Optional[str]
    detected_action: Optional[str]
    confidence: float
    reasoning: str
    raw_response: str
    model_used: Optional[str] = None


def process_dashboard_image(image_bytes: bytes, user_prompt: str) -> VisionExtraction:
    """
    Call Anthropic vision to interpret the dashboard screenshot.

    Attempts the configured model first, then a list of fallbacks so that the UI
    does not break when Anthropic deprecates a specific dated model.
    """

    if not image_bytes:
        raise VisionProcessingError("Uploaded image is empty.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise VisionProcessingError(
            "ANTHROPIC_API_KEY is required for multimodal processing."
        )

    media_type = _detect_media_type(image_bytes)
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    client = _get_client(api_key)

    prompt = (
        "You are Movi's transport assistant vision tool. Inspect the screenshot of a bus "
        "dashboard and identify the specific trip, vehicle, or deployment the user is "
        "referring to. Respond ONLY with compact JSON {\"trip_name\": str|null, "
        "\"detected_action\": str|null, \"confidence\": float between 0 and 1, "
        '"reasoning": str}. The screenshot may highlight a row using a marker or arrow.'
    )

    models_to_try = _ordered_models()
    last_exc: Optional[Exception] = None

    for model in models_to_try:
        try:
            response = _invoke_vision_model(
                client=client,
                model=model,
                prompt=prompt,
                user_prompt=user_prompt,
                encoded_image=encoded_image,
                media_type=media_type,
            )
        except Exception as exc:  # pragma: no cover - network compat
            exc_str = str(exc).lower()
            if "not_found" in exc_str or "model:" in exc_str:
                logger.warning("Vision model %s unavailable, trying fallback.", model)
                last_exc = exc
                continue
            logger.warning("Vision API call failed for model %s: %s", model, exc)
            raise VisionProcessingError("Unable to process the screenshot right now.") from exc

        raw_text = _collect_text(response)
        parsed = _parse_json_payload(raw_text)

        return VisionExtraction(
            trip_name=_safe_str(parsed.get("trip_name")),
            detected_action=_safe_str(parsed.get("detected_action")),
            confidence=_safe_float(parsed.get("confidence")),
            reasoning=_safe_str(parsed.get("reasoning")) or "Vision result returned no reasoning.",
            raw_response=raw_text,
            model_used=model,
        )

    raise VisionProcessingError(
        "Vision model unavailable. Set ANTHROPIC_VISION_MODEL to a supported model."
    ) from last_exc


def _get_client(api_key: str) -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=api_key)
    return _anthropic_client


def _ordered_models() -> list[str]:
    preferred = os.getenv("ANTHROPIC_VISION_MODEL")
    models: list[str] = []
    for candidate in [preferred, *VISION_DEFAULTS]:
        if candidate and candidate not in models:
            models.append(candidate)
    return models or ["claude-3-5-sonnet-latest"]


def _invoke_vision_model(
    client: Anthropic,
    model: str,
    prompt: str,
    user_prompt: str,
    encoded_image: str,
    media_type: str,
) -> Message:
    return client.messages.create(
        model=model,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}\nUser request: {user_prompt}"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_image,
                        },
                    },
                ],
            }
        ],
    )


def _detect_media_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _collect_text(message: Message) -> str:
    parts: list[str] = []
    for block in message.content or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _parse_json_payload(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {}

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if fenced_match:
        raw_text = fenced_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if brace_match:
            raw_text = brace_match.group(0)

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning("Vision response not JSON: %s", raw_text)
        return {
            "trip_name": None,
            "detected_action": None,
            "confidence": 0.0,
            "reasoning": "Vision response could not be parsed.",
        }


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["VisionExtraction", "VisionProcessingError", "process_dashboard_image"]


