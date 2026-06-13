"""Shared OpenAI helper for the AI endpoints.

careplan_llm.py predates this and stays self-contained; every NEW Phase-5
endpoint (simplify, med-safety, lab-analyze, insights, chat) goes through here
so they share one client, one JSON-parsing path, and one error style.
"""

import json
from openai import OpenAI

from .config import settings


def get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Put it in .env")
    return OpenAI(api_key=settings.openai_api_key)


def call_json(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict:
    """Call the model and return parsed JSON.

    Uses response_format=json_object so the model is constrained to valid JSON.
    Raises RuntimeError (-> 500 with a clean message) if parsing fails.
    """
    client = get_client()
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or ""
    try:
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(
            f"LLM output was not valid JSON. Error: {e}\nRaw:\n{content[:2000]}"
        )
