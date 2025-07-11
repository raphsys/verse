from pydantic import BaseModel, Field
from typing import Optional

class DocumentUploadResponse(BaseModel):
    original_text: str
    translated_text: str
    language_detected: Optional[str] = None
    provider: str


