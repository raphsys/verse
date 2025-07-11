"""
extractor.py
------------
Fonctions utilitaires pour extraire le texte de fichiers PDF, DOCX et TXT.
"""

import os
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(filepath):
    """
    Extrait le texte brut d'un fichier PDF.
    """
    text = []
    with open(filepath, "rb") as f:
        pdf = PdfReader(f)
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text).strip()

def extract_text_from_docx(filepath):
    """
    Extrait le texte brut d'un fichier DOCX.
    """
    doc = Document(filepath)
    text = [para.text for para in doc.paragraphs]
    return "\n".join(text).strip()

def extract_text_from_txt(filepath):
    """
    Extrait le texte d'un fichier TXT.
    """
    with open(filepath, encoding="utf-8") as f:
        return f.read().strip()

def extract_text(filepath):
    """
    Extrait le texte du fichier donné selon son extension.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext == ".docx":
        return extract_text_from_docx(filepath)
    elif ext == ".txt":
        return extract_text_from_txt(filepath)
    else:
        raise ValueError(f"Type de fichier non supporté: {ext}")

