from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.translation import Translation
from app.schemas.translation import TranslateRequest, TranslateResponse, TranslationHistoryItem
from app.utils.translation_providers import get_translator
from app.routes.users import get_current_user
from app.utils.quotas import quota_remaining, QUOTA_PER_DAY

router = APIRouter(
    prefix="/translate",
    tags=["translate"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TranslateResponse)
def translate(
    request: TranslateRequest,
    provider: str = "libre",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    remaining, today_count = quota_remaining(db, current_user.id)
    if remaining <= 0:
        raise HTTPException(
            429, f"Quota journalier atteint ({QUOTA_PER_DAY} traductions par jour). Réessayez demain."
        )
    translator = get_translator(provider)
    try:
        result = translator.translate(request.text, request.source_lang, request.target_lang)
    except Exception as e:
        raise HTTPException(500, f"Erreur du service de traduction : {str(e)}")
    # Enregistrement dans l'historique
    db_translation = Translation(
        user_id=getattr(current_user, "id", None),
        source_lang=request.source_lang or result.get("detected_source_lang") or "auto",
        target_lang=request.target_lang,
        original_text=request.text,
        translated_text=result["translated_text"],
        provider=result["provider"]
    )
    db.add(db_translation)
    db.commit()
    return TranslateResponse(**result)

@router.get("/history", response_model=list[TranslationHistoryItem])
def get_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    history = db.query(Translation)\
        .filter(Translation.user_id == current_user.id)\
        .order_by(Translation.created_at.desc())\
        .limit(100).all()
    return history

@router.get("/quota")
def get_my_quota(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    remaining, today_count = quota_remaining(db, current_user.id)
    return {
        "quota_total": QUOTA_PER_DAY,
        "quota_used": today_count,
        "quota_remaining": remaining
    }

