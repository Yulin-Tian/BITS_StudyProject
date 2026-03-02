import os
from typing import Tuple, List
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from PIL import Image

SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
SUPPORTED_TEXT_EXT = {".txt"}
SUPPORTED_DOCX_EXT = {".docx"}
SUPPORTED_PDF_EXT = {".pdf"}

def detect_type(path: str) -> str:
    ext = os.path.splitext(path.lower())[1]
    if ext in SUPPORTED_IMAGE_EXT:
        return "image"
    if ext in SUPPORTED_PDF_EXT:
        return "pdf"
    if ext in SUPPORTED_DOCX_EXT:
        return "docx"
    if ext in SUPPORTED_TEXT_EXT:
        return "text"
    return "unknown"

def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_docx(path: str) -> str:
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts).strip()

def extract_pdf_text_if_digital(path: str) -> str:
    # If PDF is "digital", pdfminer will return meaningful text.
    try:
        text = pdf_extract_text(path) or ""
        return text.strip()
    except Exception:
        return ""

def load_image(path: str) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGB")