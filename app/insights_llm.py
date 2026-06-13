"""/v1/insights — gentle, non-diagnostic health insights from the patient's
own vitals history and medication adherence (both supplied by Node).
"""

import json

from .config import settings
from .schemas import InsightsRequest, InsightsOutput
from .llm_client import call_json

DISCLAIMER = (
    "These insights describe patterns in your own logged data, not a medical "
    "assessment. They are not a diagnosis. Share them with your doctor if "
    "anything concerns you."
)

SYSTEM_PROMPT = """
You are the Active Care Engine inside a patient after-care app.

Your job: look at the patient's logged vitals and medication adherence and
describe simple, factual patterns (trends, consistency, gaps).

Safety guardrails:
- Do NOT diagnose, predict disease, or recommend treatments/medicines.
- Describe only what the data shows. No alarming language.
- Encourage good habits and discussing concerns with a doctor.
- If there is too little data, say so plainly in one insight.

Output MUST be valid JSON only.
"""

USER_PROMPT_TEMPLATE = """
Produce gentle, factual health insights from this data.

Return JSON with key:
- insights (array of objects), each with:
    title    : short heading
    detail   : 1-2 plain sentences describing the pattern
    category : one of "trend", "adherence", "lifestyle", "follow_up", "other"

Vitals history (JSON):
{vitals_history}

Medication adherence (JSON):
{adherence}
"""


def _simulated(req: InsightsRequest) -> InsightsOutput:
    return InsightsOutput(
        insights=[
            {"title": "Consistent logging", "category": "adherence",
             "detail": "(Simulation) You have been logging your readings regularly "
                       "this week. Keeping it up helps you and your doctor spot trends."},
            {"title": "Blood pressure steady", "category": "trend",
             "detail": "(Simulation) Your recent blood-pressure readings look stable "
                       "compared with earlier ones."},
        ],
        disclaimer=DISCLAIMER,
        simulated=True,
    )


def generate_insights(req: InsightsRequest) -> InsightsOutput:
    if settings.simulation_mode:
        return _simulated(req)

    data = call_json(
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(
            vitals_history=json.dumps(req.vitals_history, ensure_ascii=False),
            adherence=json.dumps(req.adherence, ensure_ascii=False),
        ),
    )
    data.setdefault("disclaimer", DISCLAIMER)
    data["simulated"] = False
    return InsightsOutput.model_validate(data)
