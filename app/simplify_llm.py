"""/v1/simplify — turn complex clinical instructions into plain language.

PATTERN-SETTER for all Phase-5 AI endpoints. Each endpoint module has:
  1. a DISCLAIMER constant (every output carries one),
  2. a SYSTEM_PROMPT with safety guardrails,
  3. a USER_PROMPT_TEMPLATE,
  4. a _simulated() canned response (used when SIMULATION_MODE=true),
  5. one public function: validates input -> returns a validated schema object.
"""

from .config import settings
from .schemas import SimplifyRequest, SimplifyOutput
from .llm_client import call_json

DISCLAIMER = (
    "This is a plain-language explanation of your existing instructions, not "
    "medical advice. It does not change your prescription. If anything is "
    "unclear, confirm with your doctor or pharmacist."
)

SYSTEM_PROMPT = """
You are the Active Care Engine inside a patient after-care app.

Your only job: rewrite the given clinical instruction in simple, plain English
that a non-medical adult can understand.

Safety guardrails:
- Do NOT diagnose, recommend new treatments, or change any dosage or medicine.
- Do NOT add information that is not in the input. Preserve the exact meaning.
- Expand a medical abbreviation ONLY if it is a common, unambiguous one
  (e.g. "BD" = twice a day, "PO" = by mouth). If unsure, keep the original term.
- Keep it short, warm, and clear. No markdown.

Output MUST be valid JSON only.
"""

USER_PROMPT_TEMPLATE = """
Rewrite this clinical instruction in plain language.

Return JSON with keys:
- simplified (string): the plain-language version for on-screen reading.
- tts_text (string): the same meaning written to be read aloud smoothly by a
  text-to-speech voice (spell out abbreviations, no symbols like "x3").

Clinical instruction:
{text}
"""


def _simulated(req: SimplifyRequest) -> SimplifyOutput:
    snippet = req.text.strip().replace("\n", " ")
    if len(snippet) > 120:
        snippet = snippet[:120] + "..."
    return SimplifyOutput(
        simplified=f"(Simulation) In simple terms: {snippet}",
        tts_text=f"Here is your instruction in plain language. {snippet}",
        disclaimer=DISCLAIMER,
        simulated=True,
    )


def simplify_instruction(req: SimplifyRequest) -> SimplifyOutput:
    if settings.simulation_mode:
        return _simulated(req)

    data = call_json(SYSTEM_PROMPT, USER_PROMPT_TEMPLATE.format(text=req.text))
    data.setdefault("disclaimer", DISCLAIMER)
    data["simulated"] = False
    return SimplifyOutput.model_validate(data)
