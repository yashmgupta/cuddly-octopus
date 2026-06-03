"""Thin wrapper around the Google Gemini API.

Includes automatic retry with exponential backoff to handle the
free-tier rate limit of gemini-2.0-flash (15 RPM, 1500/day).

Free tier comparison:
  gemini-2.5-flash →   5 RPM,   20 req/day  ← too low
  gemini-2.0-flash →  15 RPM, 1500 req/day  ← recommended
"""

import os
import time
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# gemini-2.0-flash: 15 RPM, 1500 req/day on free tier
MODEL: str = os.getenv("MODEL", "gemini-2.0-flash")

# 15 RPM → 1 call every 4s minimum; we use 5s to be safe
_MIN_CALL_GAP: float = float(os.getenv("MIN_CALL_GAP", "5"))
_MAX_RETRIES: int = 5
_last_call_ts: float = 0.0


def _is_rate_limit(exc: ClientError) -> bool:
    """Check if a ClientError is a 429 rate-limit error."""
    # The google-genai SDK exposes the HTTP code in different ways
    # depending on the version — check all known locations.
    code = (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
        or getattr(exc, "http_status", None)
    )
    if code == 429:
        return True
    # Fallback: check the string representation
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


def _get_retry_delay(exc: ClientError, default: float) -> float:
    """Extract the suggested retry delay from the error message."""
    match = re.search(r"retry.*?(\d+)s", str(exc), re.IGNORECASE)
    if match:
        return max(int(match.group(1)) + 2, default)
    return default


def _call_with_retry(contents, config) -> str:
    """Call the Gemini API, respecting the minimum gap and retrying on 429."""
    global _last_call_ts

    delay = _MIN_CALL_GAP

    for attempt in range(_MAX_RETRIES):
        # Enforce minimum gap between calls
        elapsed = time.time() - _last_call_ts
        if elapsed < _MIN_CALL_GAP:
            wait = _MIN_CALL_GAP - elapsed
            print(f"⏳ Rate-limit guard: waiting {wait:.1f}s before next call…")
            time.sleep(wait)

        try:
            _last_call_ts = time.time()
            response = _client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            return response.text.strip()

        except ClientError as exc:
            if not _is_rate_limit(exc):
                raise  # non-rate-limit error → re-raise immediately

            retry_after = _get_retry_delay(exc, delay)
            print(
                f"⚠️  429 Rate limit hit (attempt {attempt + 1}/{_MAX_RETRIES}). "
                f"Waiting {retry_after:.0f}s…"
            )
            time.sleep(retry_after)
            delay *= 2  # exponential backoff

    raise RuntimeError(f"Gemini API still rate-limited after {_MAX_RETRIES} retries.")


def chat(messages: list[dict], system: str | None = None) -> str:
    """Send a list of role/content messages and return the text response."""
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )

    config = types.GenerateContentConfig(
        system_instruction=system if system else None,
        temperature=0.1,
    )
    return _call_with_retry(contents, config)


def ask(prompt: str, system: str | None = None) -> str:
    """Convenience: send a single user prompt and return the response."""
    return chat([{"role": "user", "content": prompt}], system=system)
