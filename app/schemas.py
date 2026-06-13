from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any, Dict

class ExtractedDoc(BaseModel):
    file_name: str
    file_type: Literal["image", "pdf", "docx", "text", "unknown"]
    extracted_text: str
    extraction_method: str
    warnings: List[str] = Field(default_factory=list)

class VerifiedDoc(BaseModel):
    file_name: str
    verified_text: str
    user_notes: Optional[str] = None

class CarePlanMedication(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    duration: Optional[str] = None
    original_line: Optional[str] = None
    confidence: Optional[Literal["high", "medium", "low"]] = None

class CarePlanTask(BaseModel):
    category: Literal["medication", "follow_up", "monitoring", "lifestyle", "safety", "other"]
    instruction: str
    schedule: Optional[str] = None
    original_source: Optional[str] = None

class CarePlanOutput(BaseModel):
    safety_disclaimer: str
    clarification_questions: List[str] = Field(default_factory=list)
    medications: List[CarePlanMedication] = Field(default_factory=list)
    tasks: List[CarePlanTask] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    structured_summary: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# /v1/simplify — clinical instruction simplification (Phase 5)
# --------------------------------------------------------------------------- #
class SimplifyRequest(BaseModel):
    text: str

class SimplifyOutput(BaseModel):
    simplified: str           # plain-language version, for on-screen display
    tts_text: str             # a clean, speakable version for text-to-speech
    disclaimer: str
    simulated: bool = False   # true when produced by SIMULATION_MODE


# --------------------------------------------------------------------------- #
# /v1/lab-analyze — plain-language lab report analysis (Phase 5)
# --------------------------------------------------------------------------- #
class LabAnalyzeRequest(BaseModel):
    verified_text: str

class LabFlag(BaseModel):
    name: str
    value: Optional[str] = None
    status: Literal["normal", "high", "low", "borderline", "unknown"] = "unknown"
    note: Optional[str] = None

class LabAnalyzeOutput(BaseModel):
    summary: str
    flags: List[LabFlag] = Field(default_factory=list)
    disclaimer: str
    simulated: bool = False


# --------------------------------------------------------------------------- #
# /v1/med-safety — cross-medication safety alerts (Phase 5)
# --------------------------------------------------------------------------- #
class MedItem(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None

class MedSafetyRequest(BaseModel):
    medications: List[MedItem] = Field(default_factory=list)

class MedAlert(BaseModel):
    type: Literal["duplicate", "interaction", "dosage", "other"] = "other"
    medications: List[str] = Field(default_factory=list)
    message: str
    severity: Literal["info", "caution", "warning"] = "caution"

class MedSafetyOutput(BaseModel):
    alerts: List[MedAlert] = Field(default_factory=list)
    disclaimer: str
    simulated: bool = False


# --------------------------------------------------------------------------- #
# /v1/insights — health insights from vitals/adherence history (Phase 5)
# --------------------------------------------------------------------------- #
class InsightsRequest(BaseModel):
    user_id: Optional[str] = None
    vitals_history: List[Dict[str, Any]] = Field(default_factory=list)
    adherence: List[Dict[str, Any]] = Field(default_factory=list)

class Insight(BaseModel):
    title: str
    detail: str
    category: Literal["trend", "adherence", "lifestyle", "follow_up", "other"] = "other"

class InsightsOutput(BaseModel):
    insights: List[Insight] = Field(default_factory=list)
    disclaimer: str
    simulated: bool = False


# --------------------------------------------------------------------------- #
# /v1/chat — AI chatbot with health context (Phase 5)
# --------------------------------------------------------------------------- #
class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    message: str
    # Node injects what it has (medications, recent_vitals, active_care_plan).
    # Kept loose so Node can evolve its shape without breaking us.
    context: Optional[Dict[str, Any]] = None

class ChatOutput(BaseModel):
    reply: str
    used_context: bool = False
    disclaimer: str
    safety_flag: Optional[Literal["refused", "advised_see_doctor"]] = None
    simulated: bool = False