import os
import json
from glob import glob
from html import escape

LINE_CLUSTER_COLOR = "#1effb4"
WORD_COLOR_PDF = "#ff2828"
WORD_COLOR_OCR = "#00c8ff"
PHRASE_COLOR = "#ffd700"

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
    if block.get("alignment") in ("center", "right", "left", "justify"):
        css.append(f"text-align:{block['alignment']}")
    return "; ".join(css)

def html_for_block(block):
    style = css_style_from_block(block)
    bbox = block.get("bbox", [0,0,100,30])
    pos = (
        f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
        f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
        f"border:1.5px solid #999; padding:2px; overflow:hidden; {style}"
    )
    html = f'<div style="{pos}">'
    # Listes/puces
    meta = block.get("list_meta", {})
    if meta.get("list_type"):
        html += f'<span style="font-weight:bold">{escape(meta["char"])} </span>'
    # Formules
    if block.get("formula_data", {}).get("is_formula"):
        html += f'<span style="color:purple;">[FORMULE]</span> '
    # Sigle, liens
    if block.get("sigle"):
        html += f'<span style="color:darkred;">[SIGLE]</span> '
    if block.get("hyperlinks"):
        for l in block["hyperlinks"]:
            html += f'<a href="{escape(l["uri"])}" style="color:blue; text-decoration:underline;">🔗</a> '
    # Texte/phrases
    html += "<br>".join(escape(s) for s in block.get("sentences", []))
    html += "</div>"
    # Phrases (bboxes secondaires, jaune)
    for sub in block.get("content", []):
        for b in sub.get("bboxes", []):
            pos2 = (
                f"position:absolute; left:{b[0]}px; top:{b[1]}px; "
                f"width:{b[2]-b[0]}px; height:{b[3]-b[1]}px; "
                f"border:1.2px dashed {PHRASE_COLOR}; pointer-events:none;"
            )
            html += f'<div style="{pos2}" title="Phrase">{escape(sub.get("phrase","")[:80])}</div>'
        # (Option) Mots PDF/OCR
        for w in sub.get("words", []):
            color = WORD_COLOR_PDF if w.get("source") == "pdf" else WORD_COLOR_OCR
            wb = w["bbox"]
            pos3 = (
                f"position:absolute; left:{wb[0]}px; top:{wb[1]}px; "
                f"width:{wb[2]-wb[0]}px; height:{wb[3]-wb[1]}px; "
                f"border:1px solid {color}; opacity:0.7; pointer-events:none;"
            )
            html += f'<div style="{pos3}" title="{escape(w["text"])}"></div>'
    return html

def html_for_lines(lines):
    html = ""
    for line in lines:
        bbox = line.get("bbox", [0,0,100,20])
        pos = (
            f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
            f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
            f"border:1.2px solid {LINE_CLUSTER_COLOR}; box-shadow: 0 0 3px {LINE_CLUSTER_COLOR};"
            f"background:rgba(30,255,180,0.07);"
            f"pointer-events:none; z-index:3;"
        )
        # (Astuce: montrer le texte sur hover)
        html += (
            f'<div style="{pos}" title="{escape(line.get("text","")[:100])}">'
            f'</div>'
        )
    return html

def json2html(json_path, out_html_path, page_w=1000, page_h=1415, show_lines=True):
    with open(json_path, encoding="utf8") as f:
        data = json.load(f)
    blocks = data.get("blocks", [])
    lines = data.get("lines_extracted", []) if show_lines else []
    page_w = data.get("width", page_w)
    page_h = data.get("height", page_h)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"><title>WYSIWYG Preview</title>
<style>
body {{ background:#f6f6f6; }}
.page {{ position:relative; width:{page_w}px; height:{page_h}px; margin:20px auto; background:#fff; border:2px solid #222; }}
</style>
</head>
<body>
<div class="page">
"""
    for block in blocks:
        html += html_for_block(block)
    if lines:
        html += html_for_lines(lines)
    html += "</div></body></html>"
    with open(out_html_path, "w", encoding="utf8") as f:
        f.write(html)
    print(f"WYSIWYG HTML généré : {out_html_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WYSIWYG Preview HTML des extractions JSON")
    parser.add_argument("json_dir", help="Dossier des JSON")
    parser.add_argument("--out_dir", default=None, help="Dossier HTML (défaut : json_dir/html)")
    parser.add_argument("--hide-lines", action="store_true", help="Ne pas afficher les lignes bottom-up")
    args = parser.parse_args()
    json_files = sorted(glob(os.path.join(args.json_dir, "*.json")))
    out_dir = args.out_dir or os.path.join(args.json_dir, "html")
    os.makedirs(out_dir, exist_ok=True)
    for jf in json_files:
        page_num = os.path.basename(jf).split("_")[-1].split(".")[0]
        html_path = os.path.join(out_dir, f"page_{page_num}.html")
        json2html(jf, html_path, show_lines=not args.hide_lines)

