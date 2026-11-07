"""The ONLY place that talks to an LLM provider.

To swap provider (e.g. a Reply-provided OpenAI key), rewrite `chat()` here and
nothing else. Everything else in the app calls `chat(system, messages, json=..., effort=...)`.
"""
from __future__ import annotations

import json as jsonlib
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = os.getenv("MODEL", "claude-opus-5-5")
FALLBACK_BETA = "server-side-fallback-2026-07-01"

_client: anthropic.Anthropic | None = None


class LLMError(RuntimeError):
    """Raised when the provider fails or refuses; the caller decides the fallback."""


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=2, timeout=60.0)
    return _client


def _normalise(messages: list[dict]) -> list[dict]:
    """API needs the first message to be 'user' and roles to be user/assistant."""
    msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("content")]
    if not msgs or msgs[0]["role"] != "user":
        msgs.insert(0, {"role": "user", "content": "[Session started.]"})
    return msgs


def _extract_json(text: str):
    """Parse JSON even if the model wrapped it in ```json fences or added prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return jsonlib.loads(text)


def chat(system: str, messages: list[dict], json: bool = False, effort: str = "medium",
         max_tokens: int = 4000):
    """Send one request. Returns str, or a parsed dict when json=True.

    Raises LLMError on API failure/refusal, ValueError (json.JSONDecodeError) on bad JSON.
    """
    try:
        resp = _get_client().beta.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=_normalise(messages),
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except anthropic.APIStatusError as e:
        raise LLMError(f"API error {e.status_code}: {e.message} (request {e.request_id})") from e
    except anthropic.APIConnectionError as e:
        raise LLMError(f"Connection error: {e}") from e

    if resp.stop_reason == "refusal":
        raise LLMError("Model refused the request")

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return _extract_json(text) if json else text
