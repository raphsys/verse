#!/bin/bash

# Place-toi à la racine du projet avant d'exécuter ce script

# Activation conda : rappelle à l'utilisateur
echo "⚠️ Active ton environnement conda 'verse-env' avant de continuer !"

# Installer dépendances backend
pip install fastapi uvicorn python-multipart pydantic

# Ajouter au requirements.txt (évite doublons)
for pkg in fastapi uvicorn python-multipart pydantic; do
    if ! grep -q "$pkg" requirements.txt; then
        echo "$pkg" >> requirements.txt
    fi
done

# Structure modulaire du backend
mkdir -p backend/app/api backend/app/core backend/app/models backend/app/services backend/app/utils backend/app/uploads

# main.py (point d'entrée FastAPI)
cat << EOF > backend/app/main.py
from fastapi import FastAPI
from backend.app.api import routes

app = FastAPI(
    title="Verse - API de traduction intelligente",
    description="Backend de l'application Verse : gestion de la traduction et du format des documents.",
    version="0.1.0"
)

app.include_router(routes.router)
EOF

# routes.py (déclaration des endpoints)
cat << EOF > backend/app/api/routes.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
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
    # Crée le dossier uploads s'il n'existe pas
    os.makedirs("backend/app/uploads", exist_ok=True)
    file_location = f"backend/app/uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return JSONResponse(status_code=200, content={
        "filename": file.filename,
        "message": "Fichier reçu. Traitement à venir.",
    })
EOF

# __init__.py (pour modules)
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/core/__init__.py
touch backend/app/models/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py

# Script de démarrage
cat << EOF > backend/start.sh
#!/bin/bash
cd "\$(dirname "\$0")/app"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x backend/start.sh

# Ajout instructions backend au README
cat << 'READMEADD' >> README.md

---

## Backend Python (FastAPI) – Démarrage rapide

### Installation (à faire 1 seule fois)
Active d'abord l'environnement conda :
```bash
conda activate verse-env

