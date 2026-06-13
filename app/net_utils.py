"""Helpers for fetching documents that live on remote storage.

Anurag's Node backend stores uploaded records on Cloudinary, so the record row
holds a `file_url`, not the raw bytes. This module downloads such a URL to a
local temp file so the existing OCR pipeline (which works on file paths) can
process it unchanged.
"""

import os
import tempfile
from urllib.parse import urlparse, unquote

import requests

# Map common content types -> extension, used as a fallback when neither the
# provided file_name nor the URL path carries a usable extension.
_CONTENT_TYPE_EXT = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

_KNOWN_EXT = {
    ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".txt", ".docx",
}

DOWNLOAD_TIMEOUT = 30  # seconds


def _ext_from(name: str) -> str:
    return os.path.splitext(name.lower())[1]


def download_to_temp(file_url: str, file_name: str | None = None) -> str:
    """Download `file_url` to a temp file and return its local path.

    The local filename keeps a correct extension so `detect_type()` works.
    Raises a ValueError (-> surfaced as a clean 4xx) on download failure.
    """
    try:
        resp = requests.get(file_url, stream=True, timeout=DOWNLOAD_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not download file_url: {e}") from e

    # Decide the extension: provided file_name first, then URL path, then the
    # response content-type.
    ext = ""
    if file_name:
        ext = _ext_from(file_name)
    if ext not in _KNOWN_EXT:
        url_path = unquote(urlparse(file_url).path)
        ext = _ext_from(url_path)
    if ext not in _KNOWN_EXT:
        ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
        ext = _CONTENT_TYPE_EXT.get(ctype, "")

    base = os.path.splitext(os.path.basename(file_name))[0] if file_name else "download"
    fd, tmp_path = tempfile.mkstemp(prefix=f"ace_{base}_", suffix=ext or "")
    try:
        with os.fdopen(fd, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception:
        os.unlink(tmp_path)
        raise

    return tmp_path
