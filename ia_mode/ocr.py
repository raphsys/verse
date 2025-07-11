# verse/ia_mode/ocr.py

from PIL import Image
import pytesseract

def ocr_block(image, box, lang='eng'):
    """
    Effectue l'OCR sur une région de l'image définie par 'box' (x1, y1, x2, y2).
    Retourne le texte extrait.
    """
    x1, y1, x2, y2 = box
    cropped = image.crop((x1, y1, x2, y2))
    text = pytesseract.image_to_string(cropped, lang=lang)
    return text.strip()

def ocr_blocks(image, blocks, lang='eng'):
    """
    Effectue l'OCR sur une liste de blocs ({'box': ...}) sur une image.
    Ajoute la clé 'ocr_text' à chaque bloc du résultat.
    """
    results = []
    for block in blocks:
        if block['type'] in ['Text', 'Title', 'List', 'Table']:
            text = ocr_block(image, block['box'], lang=lang)
            block['ocr_text'] = text
        else:
            block['ocr_text'] = None
        results.append(block)
    return results

