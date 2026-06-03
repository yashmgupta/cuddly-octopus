"""Thin wrapper around the OpenAI chat completions API."""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI()
MODEL: str = os.getenv("MODEL", "gpt-4.1-mini")


def chat(messages: list[dict], system: str | None = None) -> str:
    """Send a list of messages to the LLM and return the text response.

    Args:
        messages: List of ``{"role": "user"|"assistant", "content": str}`` dicts.
        system: Optional system prompt injected as the first message.
    """
    all_messages: list[dict] = []
    if system:
        all_messages.append({"role": "system", "content": system})
    all_messages.extend(messages)
    response = _client.chat.completions.create(model=MODEL, messages=all_messages)
    return response.choices[0].message.content


def ask(prompt: str, system: str | None = None) -> str:
    """Convenience: send a single user prompt and return the response."""
    return chat([{"role": "user", "content": prompt}], system=system)
