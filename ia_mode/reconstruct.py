# verse/ia_mode/reconstruct.py

import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader

def reconstruct_pdf(json_dir, output_pdf, page_size=A4):
    """
    Reconstruit un PDF à partir des JSON extraits.
    - json_dir : dossier où sont stockés les JSON par page
    - output_pdf : chemin du PDF à générer
    - page_size : A4 ou letter (tuple largeur, hauteur)
    """
    json_files = sorted([f for f in os.listdir(json_dir) if f.endswith('.json')])
    if not json_files:
        print(f"Aucun JSON trouvé dans {json_dir}")
        return

    c = canvas.Canvas(output_pdf, pagesize=page_size)
    page_width, page_height = page_size

    for json_file in json_files:
        with open(os.path.join(json_dir, json_file), encoding="utf8") as f:
            page = json.load(f)

        blocks = page.get("blocks", [])
        # On suppose que les bboxes sont relatives à la taille du PDF d'origine
        w_ratio = page_width / page["width"] if page.get("width") else 1.0
        h_ratio = page_height / page["height"] if page.get("height") else 1.0

        for block in blocks:
            bbox = block.get("bbox", [0,0,100,100])
            x0, y0, x1, y1 = bbox
            x = x0 * w_ratio
            y = page_height - y1 * h_ratio  # PDF : origine en bas à gauche
            width = (x1 - x0) * w_ratio
            height = (y1 - y0) * h_ratio

            # Gère les blocs de texte
            if block.get("type") == "Page" or (block.get("content") and isinstance(block["content"], list)):
                for item in block.get("content", []):
                    txt = item.get("phrase", "")
                    style = item.get("font", {})
                    # Style de police de base, à améliorer
                    fontsize = style.get("size", 10) or 10
                    fontname = "Helvetica-Bold" if style.get("bold") else "Helvetica"
                    c.setFont(fontname, fontsize)
                    # Gère le wrap sommaire
                    max_width = width
                    lines = []
                    while txt:
                        for i in range(len(txt), 0, -1):
                            if c.stringWidth(txt[:i], fontname, fontsize) <= max_width or i == 1:
                                lines.append(txt[:i])
                                txt = txt[i:].lstrip()
                                break
                    for i, line in enumerate(lines):
                        c.drawString(x, y + height - fontsize * (i + 1), line)

            # Gère les images
            if block.get("images"):
                for img in block["images"]:
                    img_path = img.get("image_path")
                    if img_path and os.path.exists(img_path):
                        try:
                            c.drawImage(ImageReader(img_path), x, y, width=width, height=height, mask='auto')
                        except Exception as e:
                            print(f"[WARN] Erreur image {img_path}: {e}")

            # À venir : tableaux, liens, styles avancés…

        c.showPage()
    c.save()
    print(f"PDF reconstitué généré dans {output_pdf}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reconstruit un PDF à partir des JSON d'extraction fine")
    parser.add_argument("json_dir", help="Dossier contenant les JSON (par page)")
    parser.add_argument("--out", default="reconstruct_output.pdf", help="Chemin du PDF généré")
    parser.add_argument("--size", default="A4", help="Taille de page ('A4' ou 'letter')")
    args = parser.parse_args()

    size = A4 if args.size.upper() == "A4" else letter
    reconstruct_pdf(args.json_dir, args.out, page_size=size)

