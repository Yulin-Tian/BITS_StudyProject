import os

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

from .config import settings
from .security import require_internal_key
from .pipeline import extract_text
from .net_utils import download_to_temp
from .schemas import (
    VerifiedDoc, ExtractedDoc, SimplifyRequest,
    LabAnalyzeRequest, MedSafetyRequest, InsightsRequest, ChatRequest,
)
from .careplan_llm import generate_care_plan
from .simplify_llm import simplify_instruction
from .lab_analyze_llm import analyze_lab_report
from .med_safety_llm import check_medications
from .insights_llm import generate_insights
from .chat_llm import chat

app = FastAPI(title="Active Care Engine API", version="0.2")

DATA_DIR = os.path.join("data", "uploads")
os.makedirs(DATA_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# Error handling — match Anurag's Node convention: { "error": "<message>" }
# so his backend handles our failures the same way it handles its own.
# --------------------------------------------------------------------------- #
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "Invalid request body."})


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    # Used for clean client-facing failures (e.g. bad file_url download).
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


# --------------------------------------------------------------------------- #
# Response shaping
# --------------------------------------------------------------------------- #
def to_extract_response(extracted: ExtractedDoc) -> dict:
    """Shape the pipeline result into the agreed API contract (a superset)."""
    method = (extracted.extraction_method or "").lower()
    ocr_used = "tesseract" in method or "ocr" in method
    low_confidence = bool(extracted.warnings) or len(extracted.extracted_text.strip()) < 20
    return {
        "file_name": extracted.file_name,
        "extracted_text": extracted.extracted_text,
        "ocr_used": ocr_used,
        "low_confidence": low_confidence,
        # Extra fields (useful for debugging / the report):
        "file_type": extracted.file_type,
        "extraction_method": extracted.extraction_method,
        "warnings": extracted.warnings,
    }


# --------------------------------------------------------------------------- #
# Health check (open, no auth) — handy for Railway + uptime checks
# --------------------------------------------------------------------------- #
@app.get("/health")
async def health():
    return {"status": "ok", "service": "active-care-engine", "version": app.version}


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
class ExtractUrlRequest(BaseModel):
    file_url: str
    file_name: str | None = None


@app.post("/v1/extract", dependencies=[Depends(require_internal_key)])
async def api_extract(file: UploadFile = File(...)):
    """(b) Extract by direct multipart upload."""
    path = os.path.join(DATA_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    extracted = extract_text(path)
    return JSONResponse(to_extract_response(extracted))


@app.post("/v1/extract/url", dependencies=[Depends(require_internal_key)])
async def api_extract_url(payload: ExtractUrlRequest):
    """(a) Extract by URL — Node sends a Cloudinary file_url; we download + OCR.

    This is the path Anurag's backend should use, since records are stored on
    Cloudinary as a file_url.
    """
    tmp_path = download_to_temp(payload.file_url, payload.file_name)
    try:
        extracted = extract_text(tmp_path)
        # Preserve the human-friendly name where we have one.
        if payload.file_name:
            extracted.file_name = payload.file_name
        return JSONResponse(to_extract_response(extracted))
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Care plan generation
# --------------------------------------------------------------------------- #
@app.post("/v1/generate", dependencies=[Depends(require_internal_key)])
async def api_generate(payload: dict):
    # payload: { file_name: str, verified_text: str, user_notes: str? }
    verified = VerifiedDoc(
        file_name=payload.get("file_name", "unknown"),
        verified_text=payload.get("verified_text", ""),
        user_notes=payload.get("user_notes"),
    )
    if not verified.verified_text.strip():
        raise HTTPException(status_code=400, detail="verified_text is required.")
    plan = generate_care_plan(verified)
    return JSONResponse(plan.model_dump())


# --------------------------------------------------------------------------- #
# Clinical instruction simplification
# --------------------------------------------------------------------------- #
@app.post("/v1/simplify", dependencies=[Depends(require_internal_key)])
async def api_simplify(payload: SimplifyRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text is required.")
    return JSONResponse(simplify_instruction(payload).model_dump())


# --------------------------------------------------------------------------- #
# Lab report analysis
# --------------------------------------------------------------------------- #
@app.post("/v1/lab-analyze", dependencies=[Depends(require_internal_key)])
async def api_lab_analyze(payload: LabAnalyzeRequest):
    if not payload.verified_text.strip():
        raise HTTPException(status_code=400, detail="verified_text is required.")
    return JSONResponse(analyze_lab_report(payload).model_dump())


# --------------------------------------------------------------------------- #
# Cross-medication safety alerts
# --------------------------------------------------------------------------- #
@app.post("/v1/med-safety", dependencies=[Depends(require_internal_key)])
async def api_med_safety(payload: MedSafetyRequest):
    if not payload.medications:
        raise HTTPException(status_code=400, detail="medications list is required.")
    return JSONResponse(check_medications(payload).model_dump())


# --------------------------------------------------------------------------- #
# Health insights
# --------------------------------------------------------------------------- #
@app.post("/v1/insights", dependencies=[Depends(require_internal_key)])
async def api_insights(payload: InsightsRequest):
    return JSONResponse(generate_insights(payload).model_dump())


# --------------------------------------------------------------------------- #
# AI chatbot
# --------------------------------------------------------------------------- #
@app.post("/v1/chat", dependencies=[Depends(require_internal_key)])
async def api_chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message is required.")
    return JSONResponse(chat(payload).model_dump())
