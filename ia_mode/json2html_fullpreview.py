import os
import json
from glob import glob
from html import escape

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
        f"padding:0 2px; overflow:hidden; {style} z-index:20;"
    )
    html = f'<div style="{pos}">'
    # Puces/listes
    meta = block.get("list_meta", {})
    if meta.get("list_type"):
        html += f'<span style="font-weight:bold; font-size:1.1em;">{escape(meta["char"])} </span>'
    # Formules
    if block.get("formula_data", {}).get("is_formula"):
        html += f'<span style="color:purple; font-weight:bold;">[FORMULE]</span> '
    # Sigle
    if block.get("sigle"):
        html += f'<span style="color:darkred; font-weight:bold;">[SIGLE]</span> '
    # Liens
    if block.get("hyperlinks"):
        for l in block["hyperlinks"]:
            html += f'<a href="{escape(l["uri"])}" style="color:blue; text-decoration:underline;" target="_blank">🔗</a> '
    # Sentences
    # On affiche chaque phrase avec un <span> (meilleur placement/overflow)
    for s in block.get("sentences", []):
        html += f'<span style="display:block;">{escape(s)}</span>'
    html += "</div>"
    return html

def html_for_image(img, images_dir):
    bbox = img.get("bbox", [0,0,100,100])
    img_path = img.get("image_path", None)
    if not img_path:
        return ""
    pos = (
        f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
        f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
        f"object-fit:contain; z-index:10;"
    )
    # Relatif au HTML généré
    img_rel = os.path.relpath(img_path, os.path.dirname(images_dir))
    return f'<img src="{escape(img_rel)}" style="{pos}"/>'

def html_for_table(table, htmltables_dir):
    bbox = table.get("bbox", [0,0,200,100])
    html_path = table.get("html", None)
    if not html_path:
        return ""
    pos = (
        f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
        f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
        f"overflow:auto; background:#fff; border:1.5px solid #2aa; z-index:30;"
    )
    try:
        with open(html_path, encoding="utf8") as f:
            table_html = f.read()
    except Exception:
        table_html = "[Erreur table]"
    return f'<div style="{pos}">{table_html}</div>'

def html_for_lines(lines):
    html = ""
    for line in lines:
        bbox = line.get("bbox", [0,0,100,20])
        pos = (
            f"position:absolute; left:{bbox[0]}px; top:{bbox[1]}px; "
            f"width:{bbox[2]-bbox[0]}px; height:{bbox[3]-bbox[1]}px; "
            f"border:1.2px dashed #1effb4; background:rgba(30,255,180,0.08); pointer-events:none; z-index:12;"
        )
        html += f'<div style="{pos}" title="{escape(line.get("text","")[:100])}"></div>'
    return html

def page_div(page_num, page_json, images_dir, htmltables_dir, show_text=True, show_images=True, show_tables=True, show_lines=True):
    # Fond = image de la page (extrait par extraction.py)
    page_img = os.path.join(images_dir, f"page_{page_num}.png")
    page_w = page_json.get("width", 1000)
    page_h = page_json.get("height", 1415)
    page_img_rel = os.path.relpath(page_img, os.path.dirname(images_dir))
    html = (
        f'<div class="page" id="page_{page_num}" style="display:none; width:{page_w}px; height:{page_h}px; '
        f'background:url(\'{page_img_rel}\'); background-size:100% 100%; background-repeat:no-repeat;">\n'
    )
    # Blocs textes/phrases
    if show_text:
        for block in page_json.get("blocks", []):
            html += html_for_block(block)
    # Images
    if show_images:
        for img in page_json.get("images", []):
            html += html_for_image(img, images_dir)
    # Tables
    if show_tables:
        for table in page_json.get("tables", []):
            html += html_for_table(table, htmltables_dir)
    # Lignes reconstituées (overlay)
    if show_lines:
        html += html_for_lines(page_json.get("lines_extracted", []))
    html += "\n</div>\n"
    return html

def jsons2html(json_files, out_html_path, images_dir, htmltables_dir, show_text=True, show_images=True, show_tables=True, show_lines=True):
    pages = []
    for jf in sorted(json_files):
        with open(jf, encoding="utf8") as f:
            pages.append(json.load(f))
    if not pages:
        print("Aucune page à prévisualiser.")
        return
    page_w = pages[0].get("width", 1000)
    page_h = pages[0].get("height", 1415)
    nb_pages = len(pages)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"><title>Aperçu Multi-page WYSIWYG Extraction</title>
<style>
body {{ background:#f6f6f6; }}
.page {{ position:relative; margin:20px auto; background:#fff; border:2px solid #222; transition:all .15s; }}
#nav {{
  position:fixed; top:10px; left:50%; transform:translateX(-50%);
  background:white; border-radius:8px; padding:8px 30px 8px 20px; box-shadow:0 2px 10px #ccc; z-index:1000;
}}
button {{ margin: 0 12px; font-size:18px; }}
</style>
<script>
let curPage = 1;
function showPage(n) {{
    let pages = document.getElementsByClassName("page");
    if (n < 1 || n > pages.length) return;
    for(let i=0;i<pages.length;i++) pages[i].style.display = "none";
    pages[n-1].style.display = "block";
    document.getElementById("curpage").textContent = n + "/" + pages.length;
    curPage = n;
}}
function prevPage() {{
    showPage(curPage-1);
}}
function nextPage() {{
    showPage(curPage+1);
}}
window.onload = function() {{
    showPage(1);
    document.addEventListener("keydown", function(e) {{
        if(e.key==="ArrowLeft") prevPage();
        if(e.key==="ArrowRight") nextPage();
    }});
}}
</script>
</head>
<body>
<div id="nav">
  <button onclick="prevPage()">&lt; Précédent</button>
  <span id="curpage">1/{nb_pages}</span>
  <button onclick="nextPage()">Suivant &gt;</button>
</div>
"""
    for i, page_json in enumerate(pages, 1):
        html += page_div(i, page_json, images_dir, htmltables_dir, show_text, show_images, show_tables, show_lines)
    html += "</body></html>"
    with open(out_html_path, "w", encoding="utf8") as f:
        f.write(html)
    print(f"Aperçu multi-page WYSIWYG généré : {out_html_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aperçu HTML WYSIWYG multi-pages complet (PDF-like)")
    parser.add_argument("json_dir", help="Dossier des JSON")
    parser.add_argument("--images_dir", help="Dossier des images de pages")
    parser.add_argument("--htmltables_dir", help="Dossier des HTML tables extraites")
    parser.add_argument("--out", default="preview_wysiwyg.html", help="Fichier HTML final")
    parser.add_argument("--hide-text", action="store_true", help="Masquer le texte (pour overlay pur)")
    parser.add_argument("--hide-images", action="store_true", help="Masquer les images extraites")
    parser.add_argument("--hide-tables", action="store_true", help="Masquer les tableaux extraits")
    parser.add_argument("--hide-lines", action="store_true", help="Masquer les lignes bottom-up")
    args = parser.parse_args()
    json_files = sorted(glob(os.path.join(args.json_dir, "*.json")))
    if not json_files:
        print("Aucun fichier JSON trouvé.")
    else:
        images_dir = args.images_dir or os.path.join(args.json_dir, "../images")
        htmltables_dir = args.htmltables_dir or os.path.join(args.json_dir, "../htmltables")
        jsons2html(
            json_files, args.out, images_dir, htmltables_dir,
            show_text=not args.hide_text,
            show_images=not args.hide_images,
            show_tables=not args.hide_tables,
            show_lines=not args.hide_lines
        )

