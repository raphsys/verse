import os
import json
from PIL import Image
from html import escape

BLOCK_COLORS = {
    "Text": "#85ea7e80",      # vert semi-transparent
    "Title": "#71aaff90",     # bleu semi-transparent
    "List": "#ffb94e85",      # orange
    "Table": "#ffe11970",     # jaune
    "Figure": "#ff696190",    # rouge
    "Unknown": "#99999950"
}

def css_style_from_block(block):
    style = block.get("style", {})
    css = []
    if style.get("font_name"):
        css.append(f"font-family:'{style['font_name']}'")
    if style.get("font_size"):
        css.append(f"font-size:{style['font_size']}pt")
    if style.get("bold"):
        css.append("font-weight:bold")
    if style.get("italic"):
        css.append("font-style:italic")
    if style.get("underline"):
        css.append("text-decoration:underline")
    if style.get("color"):
        css.append(f"color:rgb{style['color']}")
    if block.get("alignment") in ("center","right","left","justify"):
        css.append(f"text-align:{block['alignment']}")
    return "; ".join(css)

def html_for_block(block, highlight_nontrans=False, highlight_types=None, show_score=False):
    style = css_style_from_block(block)
    bbox = block.get("bbox", [0,0,100,30])
    btype = block.get("type", "Unknown")
    color = BLOCK_COLORS.get(btype, "#99999950")
    if highlight_types and btype not in highlight_types:
        return ""  # filtrage de types
    pos = (
        f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
        f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
        f"background:{color}; border:1.5px solid #3336; box-sizing:border-box; overflow:hidden; {style}"
    )
    extra = []
    if block.get("non_translatable"):
        pos += "box-shadow:0 0 6px 3px #fa3;"
        if highlight_nontrans:
            extra.append('<span style="background:#fa3; color:#000; font-size:10pt;">[NON-TRAD]</span>')
    if block.get("formula_data", {}).get("is_formula"):
        extra.append('<span style="color:purple; font-weight:bold;">[FORMULE]</span>')
    if block.get("sigle"):
        extra.append('<span style="color:darkred;">[SIGLE]</span>')
    score = block.get("score", 1.0)
    if show_score:
        extra.append(f"<span style='font-size:10pt; color:#888'>({score:.2f})</span>")
    # contenu textuel
    txt = "<br>".join(escape(s) for s in block.get("sentences", []))
    html = f'<div style="{pos}">{" ".join(extra)}<br>{txt}</div>'
    return html

def overlay_html(image_path, json_path, out_html, highlight_types=None, highlight_nontrans=False, show_score=False):
    with open(json_path, encoding="utf8") as f:
        data = json.load(f)
    blocks = data.get("blocks", [])
    # image : taille réelle
    image = Image.open(image_path)
    w, h = image.size
    # HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Overlay WYSIWYG</title>
<style>
body {{ background:#f6f6f6; }}
.page-bg {{
    position:relative;
    width:{w}px; height:{h}px;
    margin:20px auto;
    background:#fff;
    border:2px solid #222;
    background-image:url('{os.path.basename(image_path)}');
    background-size:100% 100%;
}}
.block-div {{ pointer-events:none; }}
</style>
</head>
<body>
<div class="page-bg">
"""
    for block in blocks:
        html += html_for_block(
            block,
            highlight_nontrans=highlight_nontrans,
            highlight_types=highlight_types,
            show_score=show_score
        )
    html += "</div></body></html>"

    # Copie l'image à côté si besoin
    out_dir = os.path.dirname(out_html)
    os.makedirs(out_dir, exist_ok=True)
    out_img_path = os.path.join(out_dir, os.path.basename(image_path))
    if not os.path.exists(out_img_path):
        image.save(out_img_path)

    with open(out_html, "w", encoding="utf8") as f:
        f.write(html)
    print(f"Overlay HTML WYSIWYG généré : {out_html}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Overlay HTML WYSIWYG (image + blocs)")
    parser.add_argument("--img", required=True, help="Image PNG de la page (output/images/page_X.png)")
    parser.add_argument("--json", required=True, help="Fichier JSON extrait de la page")
    parser.add_argument("--out", required=True, help="Chemin du HTML de sortie")
    parser.add_argument("--type", type=str, default=None,
                        help="Types de blocs à afficher (ex: Text,Title,Table,Figure, séparés par virgule)")
    parser.add_argument("--highlight-nontrans", action="store_true", help="Surligner zones non traduisibles")
    parser.add_argument("--show-score", action="store_true", help="Afficher le score de confiance IA")
    args = parser.parse_args()

    highlight_types = None
    if args.type:
        highlight_types = [t.strip() for t in args.type.split(",")]
    overlay_html(
        args.img,
        args.json,
        args.out,
        highlight_types=highlight_types,
        highlight_nontrans=args.highlight_nontrans,
        show_score=args.show_score
    )

