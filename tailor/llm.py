"""Thin wrapper around the Gemini API free tier (google-genai SDK).
Get a free key at https://aistudio.google.com/apikey and set GEMINI_API_KEY.

Defaults to a Gemma model rather than a Gemini-branded one: some Google
accounts get 0 free-tier quota for gemini-*-flash (account/region-gated,
not a per-key issue — confirmed by testing a freshly created key/project
that hit the same limit) while still having working quota for Gemma models.
If your account has full Gemini free tier access, override via GEMINI_MODEL
in .env, e.g. GEMINI_MODEL=gemini-2.0-flash.
"""

import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = os.environ.get("GEMINI_MODEL", "gemma-4-26b-a4b-it")

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey and add it to your .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def generate_text(prompt, system_instruction=None):
    config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
    resp = _get_client().models.generate_content(model=MODEL, contents=prompt, config=config)
    return resp.text


def generate_json(prompt, system_instruction=None):
    """Asks the model for strict JSON output and parses it."""
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
    )
    resp = _get_client().models.generate_content(model=MODEL, contents=prompt, config=config)
    return json.loads(resp.text)
