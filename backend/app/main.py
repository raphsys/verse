"""
main.py
-------
Point d'entrée principal FastAPI. Importe et enregistre les routers.
"""
from fastapi import FastAPI
from app.db import init_db
from app.routes.users import router as users_router
from app.routes.translate import router as translate_router
from app.routes.documents import router as documents_router

app = FastAPI(
    title="API Utilisateur & Traduction",
    description="Inscription, connexion, traduction IA, etc.",
    version="1.1.0"
)

init_db()
app.include_router(users_router)
app.include_router(translate_router)
app.include_router(documents_router)
