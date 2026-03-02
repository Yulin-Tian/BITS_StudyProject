from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    poppler_path: str = os.getenv("POPPLER_PATH", "")
    ocr_lang: str = os.getenv("OCR_LANG", "eng")

settings = Settings()