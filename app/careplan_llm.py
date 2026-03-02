import json
from openai import OpenAI
from .config import settings
from .schemas import VerifiedDoc, CarePlanOutput

SYSTEM_PROMPT = """
You are the Active Care Engine inside a patient after-care app.

Safety guardrails:
- Do NOT diagnose.
- Do NOT recommend new treatments, new medicines, dosage changes, or stopping medicines.
- Only transform the provided prescription/record text into:
  1) a structured plan and reminders,
  2) plain-language explanations,
  3) clarification questions when information is missing/ambiguous.
- If the text does not contain something, set fields to null and ask a question.
- Always include a clear safety disclaimer: user must confirm with clinician/pharmacist.

Output MUST be valid JSON only (no markdown).
"""

USER_PROMPT_TEMPLATE = """
Input is OCR-verified medical text (typed, English). Convert into a structured after-care plan.

Return JSON with keys:
- safety_disclaimer (string)
- clarification_questions (array of strings)
- medications (array of objects with: name, strength, form, dosage, frequency, timing, duration, original_line, confidence)
- tasks (array of objects with: category, instruction, schedule, original_source)
- red_flags (array of strings)
- structured_summary (object; you may include follow_up, monitoring, lifestyle, notes)

Important:
- Use only what is written.
- Timing mapping may be suggested ONLY if it is a common expansion of abbreviations found in the text, and mark confidence medium/low.
- Always preserve original_line so user can verify.

Verified text:
{verified_text}

User notes (optional):
{user_notes}
"""
def normalize_task_category(cat: str) -> str:
    if not cat:
        return "other"
    c = cat.strip().lower()

    mapping = {
        "self-care": "lifestyle",
        "self care": "lifestyle",
        "selfcare": "lifestyle",
        "care": "lifestyle",
        "home care": "lifestyle",

        "monitoring": "monitoring",
        "follow-up": "follow_up",
        "follow up": "follow_up",
        "followup": "follow_up",

        "medication": "medication",
        "medicine": "medication",
        "drugs": "medication",

        "safety": "safety",
        "warning": "safety",
        "red flags": "safety",
    }

    return mapping.get(c, "other")

def generate_care_plan(verified: VerifiedDoc) -> CarePlanOutput:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY missing. Put it in .env")

    client = OpenAI(api_key=settings.openai_api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        verified_text=verified.verified_text,
        user_notes=verified.user_notes or ""
    )

    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""
    try:
        data = json.loads(content)
    except Exception as e:
        raise RuntimeError(
        f"LLM output was not valid JSON. Error: {e}\nRaw:\n{content[:2000]}"
    )

    # Normalize task categories to match schema
    if isinstance(data, dict) and "tasks" in data and isinstance(data["tasks"], list):
        for t in data["tasks"]:
            if isinstance(t, dict):
                t["category"] = normalize_task_category(t.get("category", ""))

    return CarePlanOutput.model_validate(data)
    