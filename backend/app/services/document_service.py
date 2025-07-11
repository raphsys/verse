import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verse")

def mock_translate(file_path):
    logger.info(f"Traitement du fichier {file_path} (mock)")
    detected_text = f"Texte extrait du fichier : {file_path}"
    translated_text = detected_text[::-1]  # Simple inversion de chaîne pour démo
    return detected_text, translated_text
