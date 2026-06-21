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


def _clean_history(history, limit: int = 10) -> list:
    """Keep only well-formed {role: user|assistant, content: str} turns, last N."""
    cleaned = []
    for turn in (history or []):
        if not isinstance(turn, dict):
            continue
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            cleaned.append({"role": role, "content": content})
    return cleaned[-limit:]


def call_json(system_prompt: str, user_prompt: str, temperature: float = 0.2,
              history=None) -> dict:
    """Call the model and return parsed JSON.

    Uses response_format=json_object so the model is constrained to valid JSON.
    `history` (optional) is a list of prior {role, content} turns inserted
    between the system prompt and the final user prompt, for multi-turn chat.
    Raises RuntimeError (-> 500 with a clean message) if parsing fails.
    """
    client = get_client()
    messages = [{"role": "system", "content": system_prompt.strip()}]
    messages.extend(_clean_history(history))
    messages.append({"role": "user", "content": user_prompt.strip()})
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
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
