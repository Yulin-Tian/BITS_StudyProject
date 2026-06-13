from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")
    poppler_path: str = os.getenv("POPPLER_PATH", "")
    ocr_lang: str = os.getenv("OCR_LANG", "eng")

    # Shared secret that Anurag's Node backend must send in the X-Internal-Key
    # header. If left empty (dev), auth is open; once set, every call is checked.
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "")

    # When true, AI endpoints return realistic canned JSON without calling
    # OpenAI. Use for demos, no-key situations, and saving cost while testing.
    simulation_mode: bool = _as_bool(os.getenv("SIMULATION_MODE", "false"))

settings = Settings()