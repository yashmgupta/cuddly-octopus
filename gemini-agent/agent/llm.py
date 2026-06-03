"""Thin wrapper around the Google Gemini API.

Includes automatic retry with exponential backoff to handle the
free-tier rate limit of 5 RPM on gemini-2.5-flash.
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
MODEL: str = os.getenv("MODEL", "gemini-2.5-flash")

# Free tier = 5 RPM → wait at least 12s between calls.
# Retry up to MAX_RETRIES times on 429, doubling the wait each time.
_MIN_CALL_GAP: float = float(os.getenv("MIN_CALL_GAP", "12"))
_MAX_RETRIES: int = 5
_last_call_ts: float = 0.0


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
            if exc.status_code != 429:
                raise  # non-rate-limit error → re-raise immediately

            # Try to read retryDelay from the error details
            retry_after = delay
            msg = str(exc)
            match = re.search(r"retry.*?(\d+)s", msg, re.IGNORECASE)
            if match:
                retry_after = max(int(match.group(1)) + 2, delay)

            print(f"⚠️  429 Rate limit hit (attempt {attempt + 1}/{_MAX_RETRIES}). "
                  f"Waiting {retry_after:.0f}s…")
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
