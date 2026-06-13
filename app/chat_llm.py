"""/v1/chat — the AI health chatbot. Answers patient questions in plain
language, grounded in the health context Node injects (medications, recent
vitals, active care plan). Non-diagnostic, with safety guardrails.
"""

import json

from .config import settings
from .schemas import ChatRequest, ChatOutput
from .llm_client import call_json

DISCLAIMER = (
    "I'm an assistant for general information about your own care record, not a "
    "doctor. I can't diagnose or change your treatment. For anything urgent or "
    "uncertain, please contact your doctor or pharmacist."
)

SYSTEM_PROMPT = """
You are Curastra's after-care assistant chatting with a patient.

You may use the provided health context (their medications, recent vitals,
active care plan) to give helpful, personalised, plain-language answers about
their EXISTING care.

Safety guardrails (critical):
- Do NOT diagnose, and do NOT recommend new treatments, medicines, or dosage
  changes. Do not interpret symptoms as a specific disease.
- If asked to do any of the above, politely decline and set safety_flag to
  "refused", explaining you can't and suggesting they ask their clinician.
- If the question describes possible emergency or worrying symptoms (e.g. chest
  pain, trouble breathing, severe bleeding), advise seeking medical help and set
  safety_flag to "advised_see_doctor".
- Only use facts from the provided context; never invent medications or values.
- Be warm, brief, and clear.

Output MUST be valid JSON only.
"""

USER_PROMPT_TEMPLATE = """
Patient message:
{message}

Health context (JSON; may be empty):
{context}

Return JSON with keys:
- reply (string): your plain-language answer.
- safety_flag (string or null): null normally, "refused" if you declined a
  diagnosis/treatment request, or "advised_see_doctor" for possible emergencies.
"""


def _simulated(req: ChatRequest, used_context: bool) -> ChatOutput:
    return ChatOutput(
        reply=f"(Simulation) Thanks for your question. Based on your care record, "
              f"here's a general answer to: \"{req.message.strip()[:100]}\". "
              f"Please confirm anything important with your doctor.",
        used_context=used_context,
        disclaimer=DISCLAIMER,
        safety_flag=None,
        simulated=True,
    )


def chat(req: ChatRequest) -> ChatOutput:
    used_context = bool(req.context)

    if settings.simulation_mode:
        return _simulated(req, used_context)

    context_json = json.dumps(req.context or {}, ensure_ascii=False)
    data = call_json(
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(message=req.message, context=context_json),
        temperature=0.3,
    )
    return ChatOutput(
        reply=data.get("reply", ""),
        used_context=used_context,
        disclaimer=DISCLAIMER,
        safety_flag=data.get("safety_flag"),
        simulated=False,
    )
