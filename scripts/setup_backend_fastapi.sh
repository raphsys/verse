#!/bin/bash

# Se placer à la racine du projet (adapter si besoin)
cd "$(dirname "$0")"

# Activation de l'environnement conda - à faire manuellement si ce n'est pas déjà actif !
echo "⚠️ Pense à activer ton environnement conda 'verse-env' AVANT de lancer ce script."

# Installation des dépendances FastAPI et Uvicorn
pip install fastapi uvicorn

# Ajout dans requirements.txt
pip freeze | grep -E 'fastapi|uvicorn' >> requirements.txt

# Création du squelette backend
mkdir -p backend/app

cat << EOF > backend/app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Verse - API de traduction intelligente",
    description="Backend de l'application Verse (traduction et préservation de formats)",
    version="0.1.0"
)

@app.get("/")
def lire_racine():
    return {"message": "Bienvenue sur l'API Verse !"}
EOF

# Script de lancement rapide
cat << EOF > backend/start.sh
#!/bin/bash
cd "\$(dirname "\$0")/app"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF
chmod +x backend/start.sh

# Mise à jour du README
cat << 'ADD' >> README.md

---

## Backend Python - FastAPI

### Installation des dépendances

Active d'abord l'environnement conda :
\`\`\`bash
conda activate verse-env
\`\`\`

Installe FastAPI et Uvicorn :
\`\`\`bash
pip install fastapi uvicorn
\`\`\`

### Lancement du backend

Depuis la racine du projet :
\`\`\`bash
cd backend
./start.sh
\`\`\`
Puis va sur [http://localhost:8000/docs](http://localhost:8000/docs) pour explorer l'API interactive.

Le code principal du backend se trouve dans \`backend/app/main.py\`.

---
ADD

echo "✅ FastAPI backend prêt ! Lance './backend/start.sh' pour tester l'API sur http://localhost:8000"

