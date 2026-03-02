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