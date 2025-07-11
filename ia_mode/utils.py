# verse/ia_mode/utils.py

from pdf2image import convert_from_path
from PIL import Image
import os

def pdf_to_images(pdf_path, dpi=300, out_dir=None):
    """
    Convertit un PDF en une liste d'images PIL.Image (une par page).
    Si out_dir est renseigné, sauvegarde aussi chaque image en PNG dans ce dossier.
    """
    images = convert_from_path(pdf_path, dpi=dpi)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        for idx, img in enumerate(images):
            img_path = os.path.join(out_dir, f"page_{idx+1}.png")
            img.save(img_path)
    return images

def save_images(images, out_dir):
    """
    Sauvegarde une liste d'images PIL.Image dans un dossier donné.
    """
    os.makedirs(out_dir, exist_ok=True)
    for idx, img in enumerate(images):
        img.save(os.path.join(out_dir, f"page_{idx+1}.png"))

