# verse

Projet open source de traduction intelligente avec préservation du format des documents et extensions multimodales (texte, images, vidéos).

## Structure du projet
- **src/** : code source principal
- **backend/** : API, traitement IA, etc.
- **frontend/** : interface utilisateur
- **docs/** : documentation technique et utilisateur
- **tests/** : scripts de tests
- **scripts/** : utilitaires divers
- **data/** : jeux de données, exemples
- **notebooks/** : analyses et prototypes Jupyter

## Installation rapide
```bash
git clone <repo_git>
cd verse
# Suivre la doc dans docs/
```

## Auteurs
- Raphael DOLEAGBENOU

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

---

## Backend Python (FastAPI) – Démarrage rapide

### Installation (à faire 1 seule fois)
Active d'abord l'environnement conda :
```bash
conda activate verse-env


---

## Endpoint de traduction (mock)

Un nouveau endpoint `/translate` a été ajouté.

- Permet d'uploader un document (PDF, DOCX, etc.)
- Retourne une simulation d'extraction et de traduction du texte
- Exemple d'utilisation via Swagger UI (`/docs`)

---
# verse
