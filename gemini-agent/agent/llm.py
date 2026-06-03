"""Thin wrapper around the Google Gemini API."""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL: str = os.getenv("MODEL", "gemini-2.5-flash")


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
    response = _client.models.generate_content(model=MODEL, contents=contents, config=config)
    return response.text.strip()


def ask(prompt: str, system: str | None = None) -> str:
    """Convenience: send a single user prompt and return the response."""
    return chat([{"role": "user", "content": prompt}], system=system)
