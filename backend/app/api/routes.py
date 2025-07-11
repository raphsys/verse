from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from services import document_service
import os

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Bienvenue sur l'API Verse !"}

@router.get("/status")
def status():
    return {"status": "ok", "detail": "Le backend Verse fonctionne."}

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return JSONResponse(status_code=200, content={
        "filename": file.filename,
        "message": "Fichier reçu. Traitement à venir.",
    })

@router.post("/translate")
async def translate_document(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    try:
        detected_text, translated_text = document_service.mock_translate(file_location)
        return {
            "filename": file.filename,
            "detected_text": detected_text,
            "translated_text": translated_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {str(e)}")
