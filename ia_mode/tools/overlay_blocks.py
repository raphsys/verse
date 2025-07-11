import os
import json
from PIL import Image, ImageDraw, ImageFont

COLORS = {
    "Text": (0, 200, 0),
    "Title": (0, 100, 255),
    "List": (220, 100, 0),
    "Table": (255, 0, 0),
    "Figure": (180, 0, 255),
    "default": (100, 100, 100)
}
PHRASE_COLOR = (255, 215, 0)  # Jaune clair
WORD_COLOR_PDF = (255, 40, 40)    # Rouge pâle
WORD_COLOR_OCR = (0, 200, 255)    # Cyan vif
LINE_CLUSTER_COLOR = (30, 255, 180)  # Vert turquoise (pour les lignes reconstituées)

def get_color(type_):
    return COLORS.get(type_, COLORS["default"])

def draw_blocks_on_image(
    image_path,
    json_path,
    save_path=None,
    show=True,
    max_text_len=60,
    show_words=False,
    show_source=False,
    show_lines=True
):
    img = Image.open(image_path).convert("RGBA")
    with open(json_path, encoding="utf8") as f:
        data = json.load(f)

    page_w = data.get("width", img.width)
    page_h = data.get("height", img.height)
    scale_x = img.width / page_w if page_w else 1.0
    scale_y = img.height / page_h if page_h else 1.0

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except:
        font = None
        font_small = None

    # 1. Blocs principaux (IA)
    for block in data.get("blocks", []):
        bbox = block["bbox"]
        bbox_px = [bbox[0]*scale_x, bbox[1]*scale_y, bbox[2]*scale_x, bbox[3]*scale_y]
        type_ = block.get("type", "Unknown")
        color = get_color(type_)
        draw.rectangle(bbox_px, outline=color, width=4)
        txt = f"{type_} (id={block.get('id')})"
        if font:
            draw.text((bbox_px[0]+3, bbox_px[1]+3), txt, fill=color, font=font)
        else:
            draw.text((bbox_px[0]+3, bbox_px[1]+3), txt, fill=color)
        # 2. Sous-blocs (phrases)
        for sub in block.get("content", []):
            phrase = sub.get("phrase", "")[:max_text_len].replace('\n', ' ')
            bboxes = sub.get("bboxes", [])
            for i, b in enumerate(bboxes):
                sub_bbox_px = [b[0]*scale_x, b[1]*scale_y, b[2]*scale_x, b[3]*scale_y]
                draw.rectangle(sub_bbox_px, outline=PHRASE_COLOR, width=2)
                if i == 0:
                    if font:
                        draw.text((sub_bbox_px[0]+2, sub_bbox_px[1]+2), phrase, fill=PHRASE_COLOR, font=font)
                    else:
                        draw.text((sub_bbox_px[0]+2, sub_bbox_px[1]+2), phrase, fill=PHRASE_COLOR)
            if show_words:
                for word in sub.get("words", []):
                    wb = word["bbox"]
                    color = WORD_COLOR_PDF if word.get("source") == "pdf" else WORD_COLOR_OCR
                    word_px = [wb[0]*scale_x, wb[1]*scale_y, wb[2]*scale_x, wb[3]*scale_y]
                    draw.rectangle(word_px, outline=color, width=2)
                    if show_source:
                        tag = word.get("source", "?")
                        if font_small:
                            draw.text((word_px[0]+1, word_px[1]+1), tag, fill=color, font=font_small)
                        else:
                            draw.text((word_px[0]+1, word_px[1]+1), tag, fill=color)

    # 3. (Optionnel) Affiche les lignes bottom-up (clustered lines, turquoise)
    if show_lines:
        lines_extracted = data.get("lines_extracted", [])
        for line in lines_extracted:
            bbox = line["bbox"]
            bbox_px = [bbox[0]*scale_x, bbox[1]*scale_y, bbox[2]*scale_x, bbox[3]*scale_y]
            draw.rectangle(bbox_px, outline=LINE_CLUSTER_COLOR, width=1)
            if font:
                draw.text((bbox_px[0]+1, bbox_px[1]-8), line["text"][:60], fill=LINE_CLUSTER_COLOR, font=font)
            else:
                draw.text((bbox_px[0]+1, bbox_px[1]-8), line["text"][:60], fill=LINE_CLUSTER_COLOR)

    if save_path:
        img.save(save_path)
        print(f"[OVERLAY] Saved: {save_path}")
    if show:
        img.show()

def draw_document_overlays(
    images_dir,
    json_dir,
    out_dir,
    show_words=False,
    max_text_len=60,
    show_source=False,
    show_lines=True
):
    os.makedirs(out_dir, exist_ok=True)
    for file in os.listdir(json_dir):
        if not file.startswith("page_") or not file.endswith(".json"):
            continue
        json_path = os.path.join(json_dir, file)
        page_num = int(file.replace("page_", "").replace(".json", ""))
        img_path = os.path.join(images_dir, f"page_{page_num}.png")
        if not os.path.exists(img_path):
            continue
        out_path = os.path.join(out_dir, f"overlay_{page_num}.png")
        draw_blocks_on_image(
            img_path, json_path, save_path=out_path,
            show=False, max_text_len=max_text_len,
            show_words=show_words, show_source=show_source, show_lines=show_lines
        )
        print(f"[OVERLAY] page {page_num} → {out_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Overlay blocs, phrases, (et mots/lignes) sur image (contour seul)")
    parser.add_argument("image", nargs="?", help="Image PNG de la page")
    parser.add_argument("json", nargs="?", help="Fichier JSON d'extraction")
    parser.add_argument("--out", default=None, help="Chemin de sortie (PNG)")
    parser.add_argument("--show-words", action="store_true", help="Dessiner aussi les mots individuellement")
    parser.add_argument("--show-source", action="store_true", help="Afficher la source (pdf/ocr) sur chaque mot")
    parser.add_argument("--hide-lines", action="store_true", help="Ne pas afficher les lignes bottom-up")
    parser.add_argument("--batch", action="store_true", help="Batch sur tout un dossier (images+json)")
    parser.add_argument("--images-dir", default=None, help="Dossier images (batch)")
    parser.add_argument("--json-dir", default=None, help="Dossier json (batch)")
    parser.add_argument("--out-dir", default=None, help="Dossier de sortie overlay (batch)")
    args = parser.parse_args()

    if args.batch:
        assert args.images_dir and args.json_dir and args.out_dir
        draw_document_overlays(
            args.images_dir, args.json_dir, args.out_dir,
            show_words=args.show_words, show_source=args.show_source, show_lines=not args.hide_lines
        )
    else:
        assert args.image and args.json
        draw_blocks_on_image(
            args.image, args.json, save_path=args.out, show=(args.out is None),
            show_words=args.show_words, show_source=args.show_source, show_lines=not args.hide_lines
        )

