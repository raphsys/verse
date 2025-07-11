#!/bin/bash

# -- S'assurer d'être dans le bon dossier
if [ ! -d "backend/app" ]; then
    echo "❌ Lance ce script à la racine du projet verse."
    exit 1
fi

# -- Ajout du service de "traduction"
mkdir -p backend/app/services

cat << EOF > backend/app/services/document_service.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verse")

def mock_translate(file_path):
    logger.info(f"Traitement du fichier {file_path} (mock)")
    detected_text = f"Texte extrait du fichier : {file_path}"
    translated_text = detected_text[::-1]  # Simple inversion de chaîne pour démo
    return detected_text, translated_text
EOF

# -- Ajout de l'__init__.py si non présent
touch backend/app/services/__init__.py

# -- Mise à jour du routes.py pour gérer /translate
cat << 'EOF' > backend/app/api/routes.py
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
EOF

# -- Ajout log dans le README
cat << 'READMEADD' >> README.md

---

## Endpoint de traduction (mock)

Un nouveau endpoint `/translate` a été ajouté.

- Permet d'uploader un document (PDF, DOCX, etc.)
- Retourne une simulation d'extraction et de traduction du texte
- Exemple d'utilisation via Swagger UI (`/docs`)

---
READMEADD

echo "✅ Endpoint /translate ajouté ! Redémarre ./backend/start.sh et teste sur http://localhost:8000/docs"

