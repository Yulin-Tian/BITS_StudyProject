import os
from typing import List, Tuple
from PIL import Image, ImageOps
import pytesseract

from pdf2image import convert_from_path
from .config import settings

def _configure_tesseract():
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

def preprocess_image(img: Image.Image) -> Image.Image:
    # Light preprocessing for better OCR on typed documents
    gray = ImageOps.grayscale(img)
    # Simple threshold
    bw = gray.point(lambda x: 0 if x < 160 else 255, mode="1")
    return bw.convert("L")

def ocr_image(img: Image.Image) -> str:
    _configure_tesseract()
    pre = preprocess_image(img)
    return (pytesseract.image_to_string(pre, lang=settings.ocr_lang) or "").strip()

def ocr_pdf_scanned(path: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    try:
        pages = convert_from_path(path, dpi=250, poppler_path=settings.poppler_path or None)
    except Exception as e:
        return "", [f"PDF->Image conversion failed. Install Poppler or set POPPLER_PATH. Error: {e}"]

    texts = []
    for i, page in enumerate(pages, start=1):
        try:
            texts.append(f"\n\n--- Page {i} ---\n" + ocr_image(page))
        except Exception as e:
            warnings.append(f"OCR failed on page {i}: {e}")
    return "\n".join(texts).strip(), warnings