from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from app.schemas.document import DocumentUploadResponse
from app.utils.extractors import (
    extract_text_pdf,
    extract_text_docx,
    extract_text_txt,
    extract_text_image,
)
from app.utils.translation_providers import get_translator
from app.utils.document_builders import generate_docx, generate_pdf
from app.routes.users import get_current_user
import os

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

SUPPORTED_OUTPUT = {"pdf", "docx", "txt"}

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    target_lang: str = Form(..., description="Langue cible (ex: 'en', 'fr', 'ar')"),
    provider: str = Form("libre"),
    current_user=Depends(get_current_user)
):
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        original_text = extract_text_pdf(file.file)
        ext = "pdf"
    elif filename.endswith(".docx"):
        original_text = extract_text_docx(file.file)
        ext = "docx"
    elif filename.endswith(".txt"):
        original_text = extract_text_txt(file.file)
        ext = "txt"
    elif filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
        original_text = extract_text_image(file.file)
        ext = "txt"
    else:
        raise HTTPException(415, "Type de fichier non supporté")
    if not original_text.strip():
        raise HTTPException(400, "Aucun texte détecté dans le document")
    translator = get_translator(provider)
    result = translator.translate(original_text, None, target_lang)
    return DocumentUploadResponse(
        original_text=original_text,
        translated_text=result["translated_text"],
        language_detected=result.get("detected_source_lang"),
        provider=result["provider"]
    )

@router.post("/translate-and-download")
async def translate_and_download(
    file: UploadFile = File(...),
    target_lang: str = Form(..., description="Langue cible (ex: 'en', 'fr', 'ar')"),
    provider: str = Form("libre"),
    output_format: str = Form("pdf", description="Format du fichier à générer: pdf, docx, txt"),
    current_user=Depends(get_current_user)
):
    output_format = output_format.lower()
    if output_format not in SUPPORTED_OUTPUT:
        raise HTTPException(400, f"Format {output_format} non supporté")
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        original_text = extract_text_pdf(file.file)
    elif filename.endswith(".docx"):
        original_text = extract_text_docx(file.file)
    elif filename.endswith(".txt"):
        original_text = extract_text_txt(file.file)
    elif filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
        original_text = extract_text_image(file.file)
    else:
        raise HTTPException(415, "Type de fichier non supporté")
    if not original_text.strip():
        raise HTTPException(400, "Aucun texte détecté dans le document")
    translator = get_translator(provider)
    result = translator.translate(original_text, None, target_lang)
    translated_text = result["translated_text"]
    # Génération du fichier traduit
    if output_format == "pdf":
        translated_file = generate_pdf(translated_text)
        mime = "application/pdf"
        ext = "pdf"
    elif output_format == "docx":
        translated_file = generate_docx(translated_text)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
        tmp.write(translated_text)
        tmp.close()
        translated_file = tmp.name
        mime = "text/plain"
        ext = "txt"
    out_name = f"translation_{os.path.splitext(file.filename)[0]}.{ext}"
    headers = {"Content-Disposition": f'attachment; filename="{out_name}"'}
    return FileResponse(translated_file, media_type=mime, filename=out_name, headers=headers)

