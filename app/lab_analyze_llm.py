"""/v1/lab-analyze — explain a lab report in plain language, flag out-of-range
values. Non-diagnostic: it describes, it does not interpret cause or treatment.
"""

from .config import settings
from .schemas import LabAnalyzeRequest, LabAnalyzeOutput
from .llm_client import call_json

DISCLAIMER = (
    "This is a plain-language summary of your lab report, not a diagnosis. "
    "Only your doctor can interpret what these results mean for you. Please "
    "review them together."
)

SYSTEM_PROMPT = """
You are the Active Care Engine inside a patient after-care app.

Your job: summarise a lab report in plain English and list which values fall
outside the report's own stated reference ranges.

Safety guardrails:
- Do NOT diagnose, name diseases, or suggest treatments or medicines.
- Use ONLY values and reference ranges written in the input. Never invent them.
- If a value's status is unclear, mark it "unknown".
- Be calm and factual; do not alarm the reader.

Output MUST be valid JSON only.
"""

USER_PROMPT_TEMPLATE = """
Summarise this lab report for a non-medical reader.

Return JSON with keys:
- summary (string): 2-4 plain sentences describing what the report covers.
- flags (array of objects): one per test that is notable or out of range, each
  with: name, value, status (one of: normal, high, low, borderline, unknown),
  note (short plain-language remark, no diagnosis).

Lab report text:
{verified_text}
"""


def _simulated(req: LabAnalyzeRequest) -> LabAnalyzeOutput:
    return LabAnalyzeOutput(
        summary="(Simulation) This report covers routine blood values. Most "
                "appear within range; a couple are flagged for your doctor to review.",
        flags=[
            {"name": "Hemoglobin", "value": "11.2 g/dL", "status": "low",
             "note": "Slightly below the stated range."},
            {"name": "Fasting glucose", "value": "98 mg/dL", "status": "normal",
             "note": "Within the stated range."},
        ],
        disclaimer=DISCLAIMER,
        simulated=True,
    )


def analyze_lab_report(req: LabAnalyzeRequest) -> LabAnalyzeOutput:
    if settings.simulation_mode:
        return _simulated(req)

    data = call_json(SYSTEM_PROMPT, USER_PROMPT_TEMPLATE.format(verified_text=req.verified_text))
    data.setdefault("disclaimer", DISCLAIMER)
    data["simulated"] = False
    return LabAnalyzeOutput.model_validate(data)
