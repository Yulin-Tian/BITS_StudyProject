import os
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from .pipeline import extract_text
from .schemas import VerifiedDoc
from .careplan_llm import generate_care_plan

app = FastAPI(title="Active Care Engine API", version="0.1")

DATA_DIR = os.path.join("data", "uploads")
os.makedirs(DATA_DIR, exist_ok=True)

@app.post("/v1/extract")
async def api_extract(file: UploadFile = File(...)):
    path = os.path.join(DATA_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())

    extracted = extract_text(path)
    return JSONResponse(extracted.model_dump())

@app.post("/v1/generate")
async def api_generate(payload: dict):
    # payload: { file_name: str, verified_text: str, user_notes: str? }
    verified = VerifiedDoc(
        file_name=payload.get("file_name", "unknown"),
        verified_text=payload.get("verified_text", ""),
        user_notes=payload.get("user_notes")
    )
    plan = generate_care_plan(verified)
    return JSONResponse(plan.model_dump())