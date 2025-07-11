# verse/ia_mode/translate.py

import requests

def translate_text(text, source_lang='fr', target_lang='en'):
    """
    Traduit un texte avec l’API LibreTranslate.
    (Par défaut utilise https://libretranslate.de ; pour production : déployer un serveur local.)
    """
    if not text or text.strip() == "":
        return ""
    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        return r.json()["translatedText"]
    except Exception as e:
        print(f"[translate_text] ERROR: {e}")
        return text  # En cas d’erreur, retourne le texte original

def translate_blocks(blocks, source_lang='fr', target_lang='en'):
    """
    Traduit le champ 'ocr_text' de chaque bloc et ajoute 'translated_text'.
    """
    results = []
    for block in blocks:
        if block.get("ocr_text"):
            block['translated_text'] = translate_text(block['ocr_text'], source_lang, target_lang)
        else:
            block['translated_text'] = ""
        results.append(block)
    return results

