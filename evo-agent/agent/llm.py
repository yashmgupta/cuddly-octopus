"""Thin wrapper around the OpenAI client."""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
MODEL: str = os.getenv("MODEL", "gpt-4.1-mini")


def ask_llm(prompt: str) -> str:
    """Send *prompt* to the configured model and return the text response."""
    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )
    return response.output_text
