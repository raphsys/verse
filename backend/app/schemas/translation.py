from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    source_lang: Optional[str] = Field(None, description="ex: 'fr', 'en', 'de' (optionnel)")
    target_lang: str = Field(..., description="Langue cible, ex: 'en', 'fr', 'ar'")

class TranslateResponse(BaseModel):
    translated_text: str
    provider: str
    detected_source_lang: Optional[str] = None

class TranslationHistoryItem(BaseModel):
    id: str
    source_lang: str
    target_lang: str
    original_text: str
    translated_text: str
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True

