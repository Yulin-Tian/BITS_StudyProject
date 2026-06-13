"""Internal service-to-service authentication.

Anurag's Node backend is the only caller of this engine. It sends a shared
secret in the `X-Internal-Key` header. We validate it here.

Behaviour:
- If INTERNAL_API_KEY is set in .env  -> the header must match, else 401.
- If INTERNAL_API_KEY is empty (dev)  -> auth is open (no header required),
  so local testing with curl/Postman stays frictionless.
"""

from fastapi import Header, HTTPException
from typing import Optional

from .config import settings


async def require_internal_key(
    x_internal_key: Optional[str] = Header(default=None),
) -> bool:
    expected = settings.internal_api_key
    if not expected:
        # No key configured -> open mode for local development.
        return True
    if not x_internal_key or x_internal_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing internal API key (X-Internal-Key).",
        )
    return True
