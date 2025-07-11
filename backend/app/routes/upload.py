"""
upload.py
---------
Routes pour upload de documents et extraction de texte.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.extractor import extract_text

UPLOAD_DIR = "app/uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", summary="Uploader un document et extraire le texte")
async def upload_file(file: UploadFile = File(...)):
    """
    Permet d'uploader un fichier (PDF, DOCX, TXT) et retourne le texte extrait.
    """
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extracted_text = extract_text(filepath)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'extraction: {e}")

    preview = extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else "")

    return {
        "filename": file.filename,
        "text_extrait": preview
    }

