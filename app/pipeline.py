import os
from typing import List
from .schemas import ExtractedDoc, VerifiedDoc, CarePlanOutput
from .document_reader import detect_type, read_text_file, read_docx, extract_pdf_text_if_digital, load_image
from .ocr_engine import ocr_image, ocr_pdf_scanned
from .review_cli import review_and_confirm
from .careplan_llm import generate_care_plan

def extract_text(path: str) -> ExtractedDoc:
    file_name = os.path.basename(path)
    ftype = detect_type(path)
    warnings: List[str] = []

    if ftype == "text":
        return ExtractedDoc(file_name=file_name, file_type="text",
                            extracted_text=read_text_file(path),
                            extraction_method="direct_text_read",
                            warnings=[])

    if ftype == "docx":
        return ExtractedDoc(file_name=file_name, file_type="docx",
                            extracted_text=read_docx(path),
                            extraction_method="python-docx",
                            warnings=[])

    if ftype == "pdf":
        digital_text = extract_pdf_text_if_digital(path)
        # Heuristic: if digital extraction is too short, treat as scanned and OCR
        if len(digital_text) >= 200:
            return ExtractedDoc(file_name=file_name, file_type="pdf",
                                extracted_text=digital_text,
                                extraction_method="pdfminer (digital text)",
                                warnings=[])
        scanned_text, w = ocr_pdf_scanned(path)
        return ExtractedDoc(file_name=file_name, file_type="pdf",
                            extracted_text=scanned_text,
                            extraction_method="pdf2image + tesseract (scanned)",
                            warnings=w)

    if ftype == "image":
        img = load_image(path)
        text = ocr_image(img)
        return ExtractedDoc(file_name=file_name, file_type="image",
                            extracted_text=text,
                            extraction_method="tesseract (image)",
                            warnings=[])

    return ExtractedDoc(file_name=file_name, file_type="unknown",
                        extracted_text="",
                        extraction_method="unsupported",
                        warnings=["Unsupported file type. Use PDF, DOCX, TXT, or image."])

def run_end_to_end(path: str) -> tuple[ExtractedDoc, VerifiedDoc, CarePlanOutput]:
    extracted = extract_text(path)
    if not extracted.extracted_text.strip():
        raise RuntimeError(f"No text extracted from {extracted.file_name}. Warnings: {extracted.warnings}")

    verified = review_and_confirm(extracted)
    plan = generate_care_plan(verified)
    return extracted, verified, plan