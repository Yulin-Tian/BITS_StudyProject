"""/v1/med-safety — cross-medication safety alerts (duplicates / interactions).

Conservative by design: it flags things to CHECK with a pharmacist; it never
tells the user to start, stop, or change a medicine.
"""

import json

from .config import settings
from .schemas import MedSafetyRequest, MedSafetyOutput
from .llm_client import call_json

DISCLAIMER = (
    "These are general safety flags to discuss with your doctor or pharmacist, "
    "not instructions. Do not start, stop, or change any medicine based on this. "
    "Always confirm with a professional."
)

SYSTEM_PROMPT = """
You are the Active Care Engine inside a patient after-care app.

Your job: review a list of the patient's current medications and flag possible
DUPLICATES (same drug or same class taken twice) and well-known, commonly
documented INTERACTIONS worth checking.

Safety guardrails:
- Do NOT diagnose or tell the user to start/stop/change any medicine.
- Only flag things to CHECK with a pharmacist. Frame as "worth confirming".
- If you are not confident an interaction is real and well-documented, do not
  include it. Prefer fewer, higher-quality flags. No speculation.
- If nothing notable, return an empty alerts array.

Output MUST be valid JSON only.
"""

USER_PROMPT_TEMPLATE = """
Review these medications and list safety items worth checking.

Return JSON with key:
- alerts (array of objects), each with:
    type        : one of "duplicate", "interaction", "dosage", "other"
    medications : array of the medicine names involved
    message     : short plain-language explanation of what to check
    severity    : one of "info", "caution", "warning"

Medications (JSON):
{medications}
"""


def _simulated(req: MedSafetyRequest) -> MedSafetyOutput:
    names = [m.name for m in req.medications]
    alerts = []
    if len(names) >= 2:
        alerts.append({
            "type": "interaction",
            "medications": names[:2],
            "message": f"(Simulation) Worth confirming with a pharmacist whether "
                       f"{names[0]} and {names[1]} can be taken together.",
            "severity": "caution",
        })
    return MedSafetyOutput(alerts=alerts, disclaimer=DISCLAIMER, simulated=True)


def check_medications(req: MedSafetyRequest) -> MedSafetyOutput:
    if settings.simulation_mode:
        return _simulated(req)

    meds_json = json.dumps([m.model_dump() for m in req.medications], ensure_ascii=False)
    data = call_json(SYSTEM_PROMPT, USER_PROMPT_TEMPLATE.format(medications=meds_json))
    data.setdefault("disclaimer", DISCLAIMER)
    data["simulated"] = False
    return MedSafetyOutput.model_validate(data)
