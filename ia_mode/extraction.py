import os
import json
import re
import pickle
import camelot
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import spacy

import layoutparser as lp
from typing import List, Dict, Any, Tuple

from lxml import etree

DEBUG = False

def log(msg):
    if DEBUG:
        print(msg)

LAYOUT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models_pth/faster_rcnn_R_50_FPN_3x/model_final.pth")
CONFIG_PATH = "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"
LAYOUT_MODEL = lp.Detectron2LayoutModel(
    CONFIG_PATH,
    LAYOUT_MODEL_PATH,
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
)

try:
    NER = spacy.load("fr_core_news_md")
except Exception:
    NER = spacy.load("en_core_web_sm")

def make_output_dirs(pdf_path: str) -> Dict[str, str]:
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base = os.path.join(pdf_dir, f"output_{pdf_name}")
    dirs = {
        "base": base,
        "images": os.path.join(base, "images"),
        "tables": os.path.join(base, "tables"),
        "json": os.path.join(base, "json"),
        "formulas": os.path.join(base, "formulas"),
        "overlays": os.path.join(base, "overlays"),
        "mathml": os.path.join(base, "mathml"),
        "htmltables": os.path.join(base, "htmltables"),
        "export": os.path.join(base, "export"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs

def infer_style(word: dict) -> dict:
    style = {
        "font_name": word.get("fontname", ""),
        "font_size": word.get("size", ""),
        "bold": "Bold" in word.get("fontname", "") or "bold" in word.get("fontname", ""),
        "italic": "Italic" in word.get("fontname", "") or "Oblique" in word.get("fontname", "") or "italic" in word.get("fontname", ""),
        "color": word.get("non_stroking_color", None),
        "underline": bool(re.search(r'underline', word.get("fontname", ""), re.I)),
        "strike": bool(re.search(r'strike|strikethrough', word.get("fontname", ""), re.I)),
        "superscript": "super" in word.get("fontname", "").lower(),
        "subscript": "sub" in word.get("fontname", "").lower(),
        "background_color": word.get("background_color", None),
    }
    return style

def detect_alignment(block_words: List[dict], block_bbox: List[float]) -> str:
    if not block_words:
        return "unknown"
    left_margins = [w["bbox"][0] for w in block_words]
    right_margins = [w["bbox"][2] for w in block_words]
    block_left = block_bbox[0]
    block_right = block_bbox[2]
    if all(abs(l - block_left) < 15 for l in left_margins):
        if all(abs(r - block_right) < 15 for r in right_margins):
            return "justify"
        return "left"
    elif all(abs(r - block_right) < 15 for r in right_margins):
        return "right"
    else:
        return "center"

def detect_list_type(text: str) -> dict:
    match = re.match(r"^([\u2022\-\*•·‣▪‒–—●○□■➔▶►])\s+", text)
    if match:
        return {"list_type": "bullet", "level": 1, "char": match.group(1)}
    match = re.match(r"^([0-9]+\.|[a-zA-Z]\.)\s+", text)
    if match:
        return {"list_type": "numbered", "level": 1, "char": match.group(1)}
    return {"list_type": None, "level": 0, "char": ""}

def is_formula_zone(text: str) -> bool:
    if any(token in text for token in ["=", "+", "-", "∑", "∫", "lim", "sin", "cos", "tan", "√", "^", "_", "{", "}"]):
        return True
    return bool(re.match(r'^[\d\s\w\+\-\*/\^\=\(\)\[\]\{\}\\\.,;:<>√α-ωΑ-Ω∑∫∞≈≠±×÷°µ€$§%→←↔ΔΣλπρθΩ∞]+$', text.strip()))

def extract_formula_latex(text: str) -> str:
    return f"${text.strip()}$" if text else ""

def extract_formula_mathml(text: str) -> str:
    math_el = etree.Element("math", xmlns="http://www.w3.org/1998/Math/MathML")
    mrow = etree.SubElement(math_el, "mrow")
    for c in text:
        mi = etree.SubElement(mrow, "mi")
        mi.text = c
    return etree.tostring(math_el, pretty_print=True, encoding="unicode")

def is_sigle(text: str, known_sigles=None) -> bool:
    known_sigles = known_sigles or set(["ONU", "OMS", "UNESCO", "CNAM", "WHO", "AI", "USA", "EU", "etc"])
    return text.strip().upper() in known_sigles

def extract_page_image(pdf_path: str, page_num: int, images_dir: str, dpi: int = 300) -> str:
    images = convert_from_path(pdf_path, dpi=dpi, first_page=page_num+1, last_page=page_num+1)
    image_path = os.path.join(images_dir, f"page_{page_num+1}.png")
    images[0].save(image_path)
    return image_path

def extract_tables(pdf_path: str, page_num: int, tables_dir: str, htmltables_dir: str) -> List[Dict[str, Any]]:
    tables = []
    try:
        cam_tables = camelot.read_pdf(pdf_path, pages=str(page_num+1), flavor="stream")
        for tidx, table in enumerate(cam_tables):
            table_path = os.path.join(tables_dir, f"page{page_num+1}_table{tidx+1}.csv")
            html_path = os.path.join(htmltables_dir, f"page{page_num+1}_table{tidx+1}.html")
            try:
                table.to_csv(table_path)
                table.to_html(html_path)
            except Exception:
                table_path = None
                html_path = None
            tables.append({
                "table_csv": table_path,
                "html": html_path,
                "data": getattr(table, "data", []),
                "bbox": getattr(table, "_bbox", None)
            })
    except Exception as e:
        log(f"[Camelot] Tables not found on page {page_num+1}: {e}")
    return tables

def ocr_block(image, bbox, lang='fra+eng') -> str:
    crop = image.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
    text = pytesseract.image_to_string(crop, lang=lang, config="--psm 6")
    return text.strip()

def extract_pdfplumber_features(page, images_dir: str) -> Dict[str, Any]:
    result = {
        "words": [],
        "lines": [],
        "hyperlinks": [],
        "images": [],
        "page_width": getattr(page, "width", None),
        "page_height": getattr(page, "height", None)
    }
    try:
        words = list(page.extract_words(extra_attrs=["fontname", "size"]))
        log(f"[PDFPLUMBER] {len(words)} mots détectés sur la page.")
        for w in words:
            style = infer_style(w)
            result["words"].append({
                "text": w.get("text", ""),
                "bbox": [w.get('x0', 0), w.get('top', 0), w.get('x1', 0), w.get('bottom', 0)],
                "style": style,
                "source": "pdf"
            })
    except Exception as e:
        log(f"[WARN] extract_words failed: {e}")
    if hasattr(page, "lines"):
        try:
            for l in page.lines:
                if isinstance(l, dict) and 'text' in l:
                    result["lines"].append(l['text'])
        except Exception:
            pass
    if hasattr(page, "annots"):
        try:
            for ann in page.annots or []:
                if isinstance(ann, dict) and ann.get('uri'):
                    result["hyperlinks"].append({
                        "uri": ann.get('uri'),
                        "bbox": ann.get('rect')
                    })
        except Exception:
            pass
    if hasattr(page, "images"):
        try:
            for idx, img in enumerate(page.images):
                x0, y0, x1, y1 = img.get("x0", 0), img.get("top", 0), img.get("x1", 0), img.get("bottom", 0)
                try:
                    img_crop = page.within_bbox((x0, y0, x1, y1)).to_image(resolution=300)
                    img_path = os.path.join(images_dir, f"page{getattr(page, 'page_number', 1)}_img{idx+1}.png")
                    img_crop.save(img_path, format="PNG")
                    result["images"].append({
                        "bbox": [x0, y0, x1, y1],
                        "image_path": img_path
                    })
                except Exception:
                    continue
        except Exception:
            pass
    return result

def extract_words_ocr(image_path, lang='eng+fra'):
    from PIL import Image
    import pytesseract
    image = Image.open(image_path)
    ocr_result = pytesseract.image_to_data(
        image, lang=lang, output_type=pytesseract.Output.DICT)
    words = []
    for i in range(len(ocr_result["text"])):
        text = ocr_result["text"][i]
        if text.strip():
            bbox = [
                int(ocr_result["left"][i]), int(ocr_result["top"][i]),
                int(ocr_result["left"][i] + ocr_result["width"][i]),
                int(ocr_result["top"][i] + ocr_result["height"][i])
            ]
            words.append({
                "text": text,
                "bbox": bbox,
                "style": {},
                "source": "ocr"
            })
    return words

def cluster_words_to_lines(words, y_thresh=5):
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (w['bbox'][1], w['bbox'][0]))
    lines = []
    curr_line = []
    last_y = None
    for w in words_sorted:
        y = w['bbox'][1]
        if last_y is None or abs(y - last_y) < y_thresh:
            curr_line.append(w)
        else:
            if curr_line:
                lines.append(curr_line)
            curr_line = [w]
        last_y = y
    if curr_line:
        lines.append(curr_line)
    result = []
    for line in lines:
        if not line:
            continue
        text = " ".join(w['text'] for w in line)
        x0 = min(w['bbox'][0] for w in line)
        y0 = min(w['bbox'][1] for w in line)
        x1 = max(w['bbox'][2] for w in line)
        y1 = max(w['bbox'][3] for w in line)
        result.append({
            "text": text,
            "bbox": [x0, y0, x1, y1],
            "words": line
        })
    return result

def group_words_by_block(words, block_bbox):
    return [w for w in words if
            block_bbox[0] <= w["bbox"][0] <= block_bbox[2] and
            block_bbox[1] <= w["bbox"][1] <= block_bbox[3]]

def split_lines(words: List[dict], y_thresh=2.5):
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (w['bbox'][1], w['bbox'][0]))
    lines = []
    curr_line = []
    last_y = None
    for w in words_sorted:
        y = w['bbox'][1]
        if last_y is None or abs(y - last_y) < y_thresh:
            curr_line.append(w)
        else:
            if curr_line:
                lines.append(curr_line)
            curr_line = [w]
        last_y = y
    if curr_line:
        lines.append(curr_line)
    return lines

def group_words_by_sentence_ultrafine(words, lang="fr"):
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (w['bbox'][1], w['bbox'][0]))
    text_full = " ".join(w['text'] for w in words_sorted)
    doc = NER(text_full)
    sentences = []
    start = 0
    word_offsets = []
    running = 0
    for w in words_sorted:
        l = len(w['text']) + (1 if running > 0 else 0)
        word_offsets.append((running, running + l, w))
        running += l
    for sent in doc.sents:
        sent_text = sent.text.strip()
        sent_words = []
        pointer = 0
        for ostart, oend, w in word_offsets:
            if pointer >= len(sent_text):
                break
            candidate = sent_text[pointer:pointer+len(w['text'])]
            if candidate == w['text']:
                sent_words.append(w)
                pointer += len(w['text'])
                if pointer < len(sent_text) and sent_text[pointer] == ' ':
                    pointer += 1
        lines = split_lines(sent_words)
        phrase_bboxes = []
        for line in lines:
            if line:
                x0 = min(w['bbox'][0] for w in line)
                y0 = min(w['bbox'][1] for w in line)
                x1 = max(w['bbox'][2] for w in line)
                y1 = max(w['bbox'][3] for w in line)
                phrase_bboxes.append([x0, y0, x1, y1])
        style = sent_words[0].get("style", {}) if sent_words else {}
        sentences.append({
            "phrase": sent_text,
            "bboxes": phrase_bboxes,
            "words": [{"text": w["text"], "bbox": w["bbox"], "source": w.get("source", "pdf")} for w in sent_words],
            "style": style
        })
    log(f"[ULTRA-FINE] {len(sentences)} phrases segmentées (mode multilignes).")
    return sentences

def merge_vertical_blocks(blocks: List[Dict[str, Any]], thresh: float = 15.0) -> List[Dict[str, Any]]:
    merged = []
    used = [False] * len(blocks)
    for i, blk in enumerate(blocks):
        if used[i]:
            continue
        curr = blk.copy()
        for j, other in enumerate(blocks):
            if i == j or used[j]:
                continue
            if abs(curr['bbox'][0] - other['bbox'][0]) < thresh and abs(curr['bbox'][2] - other['bbox'][2]) < thresh:
                if 0 < abs(curr['bbox'][3] - other['bbox'][1]) < 2 * thresh:
                    curr['bbox'][3] = max(curr['bbox'][3], other['bbox'][3])
                    used[j] = True
        merged.append(curr)
        used[i] = True
    return merged

def segment_blocks_layoutparser(image_path: str) -> List[Dict[str, Any]]:
    image = Image.open(image_path).convert("RGB")
    layout = LAYOUT_MODEL.detect(image)
    blocks = []
    for l in layout:
        blocks.append({
            "type": l.type,
            "bbox": [l.block.x_1, l.block.y_1, l.block.x_2, l.block.y_2],
            "score": float(l.score),
            "text": getattr(l, "text", "")
        })
    blocks = merge_vertical_blocks(blocks)
    log(f"[SEGMENT] {len(blocks)} blocs détectés par LayoutParser sur {os.path.basename(image_path)}.")
    for i, b in enumerate(blocks):
        log(f"  - Bloc {i}: type={b['type']} bbox={b['bbox']} score={b['score']:.2f}")
    return blocks

def fusion_blocks(
    blocks_ia: List[Dict[str, Any]],
    features_classic: Dict[str, Any],
    tables: List[Dict[str, Any]],
    image: Image.Image,
    mathml_dir: str = None
) -> List[Dict[str, Any]]:
    fused_blocks = []
    words = features_classic.get("words", [])
    hyperlinks = features_classic.get("hyperlinks", [])
    log(f"[FUSION] {len(blocks_ia)} blocs IA à fusionner avec {len(words)} mots détectés.")
    for block_id, block in enumerate(blocks_ia):
        bx0, by0, bx1, by1 = block["bbox"]
        block_type = block.get("type", "")
        block_words = group_words_by_block(words, block["bbox"])
        log(f"  > Bloc {block_id} ({block_type}) bbox={block['bbox']}: {len(block_words)} mots dans le bloc.")
        block_ocr_text = ""
        block_sentences = []
        block_style = {}
        block_alignment = "unknown"
        list_meta = {}
        formula_data = {}
        content = []

        if block_words:
            sentences_struct = group_words_by_sentence_ultrafine(block_words)
            for s in sentences_struct:
                links = [l for l in hyperlinks if any(l.get("bbox") == b for b in s["bboxes"])]
                mathml_str = extract_formula_mathml(s["phrase"]) if is_formula_zone(s["phrase"]) and mathml_dir else ""
                content.append({
                    "phrase": s["phrase"],
                    "bboxes": s["bboxes"],
                    "words": s["words"],
                    "style": s["style"],
                    "links": links,
                    "is_formula": is_formula_zone(s["phrase"]),
                    "is_sigle": is_sigle(s["phrase"]),
                    "non_translatable": is_sigle(s["phrase"]) or is_formula_zone(s["phrase"]),
                    "mathml": mathml_str
                })
                block_ocr_text += s["phrase"] + " "
            block_ocr_text = block_ocr_text.strip()
            block_sentences = [s["phrase"] for s in sentences_struct]
            block_style = sentences_struct[0]["style"] if sentences_struct else {}
            block_alignment = detect_alignment(block_words, block["bbox"])
            log(f"    - {len(sentences_struct)} phrases extraites dans le bloc (mode ultrafine).")
        else:
            if block_type in ["Text", "Title", "List"]:
                block_ocr_text = ocr_block(image, block["bbox"])
                block_sentences = [block_ocr_text] if block_ocr_text else []
                log(f"    -> Fallback OCR: texte détecté: {block_ocr_text[:60]}...")
                for s in block_sentences:
                    mathml_str = extract_formula_mathml(s) if is_formula_zone(s) and mathml_dir else ""
                    content.append({
                        "phrase": s,
                        "bboxes": [block["bbox"]],
                        "words": [],
                        "style": {},
                        "links": [],
                        "is_formula": is_formula_zone(s),
                        "is_sigle": is_sigle(s),
                        "non_translatable": is_sigle(s) or is_formula_zone(s),
                        "mathml": mathml_str
                    })

        if block_type == "List":
            list_meta = detect_list_type(block_ocr_text)

        if is_formula_zone(block_ocr_text):
            latex = extract_formula_latex(block_ocr_text)
            formula_img_path = None
            mathml_path = None
            try:
                crop = image.crop((bx0, by0, bx1, by1))
                dirs = os.path.dirname(image.filename)
                formula_img_path = os.path.join(dirs, f"formula_{block_id+1}_page.png")
                crop.save(formula_img_path)
                if mathml_dir:
                    mathml_str = extract_formula_mathml(block_ocr_text)
                    mathml_path = os.path.join(mathml_dir, f"formula_{block_id+1}_page.xml")
                    with open(mathml_path, "w", encoding="utf8") as fxml:
                        fxml.write(mathml_str)
                log(f"    - Formule détectée: latex={latex}, img={formula_img_path}, mathml={mathml_path}")
            except Exception as e:
                log(f"    [WARN] Sauvegarde formule échouée: {e}")
            formula_data = {
                "is_formula": True,
                "latex": latex,
                "img_path": formula_img_path,
                "mathml_path": mathml_path
            }

        block_json = {
            "id": block_id,
            "type": block_type,
            "bbox": block.get("bbox", [0,0,0,0]),
            "score": block.get("score", 1.0),
            "ocr_text": block_ocr_text,
            "sentences": block_sentences,
            "style": block_style,
            "alignment": block_alignment,
            "list_meta": list_meta,
            "formula_data": formula_data,
            "sigle": is_sigle(block_ocr_text),
            "content": content,
            "hyperlinks": [],
            "non_translatable": is_sigle(block_ocr_text) or bool(formula_data),
        }

        for c in content:
            if c.get("links"):
                block_json["hyperlinks"].extend(c["links"])
        fused_blocks.append(block_json)
    log(f"[FUSION] => {len(fused_blocks)} blocs fusionnés sur la page.")
    return fused_blocks

def build_page_json(page_num, width, height, fused_blocks, logical_structure=None, lines_extracted=None):
    return {
        "page_num": page_num + 1,
        "width": width,
        "height": height,
        "blocks": fused_blocks,
        "logical_structure": logical_structure or [],
        "lines_extracted": lines_extracted or []
    }

def export_document_json_pickle(pages_json: List[Dict[str, Any]], export_dir: str, base_name: str = "extraction_doc"):
    export_json_path = os.path.join(export_dir, f"{base_name}.json")
    export_pkl_path = os.path.join(export_dir, f"{base_name}.pkl")
    with open(export_json_path, "w", encoding="utf-8") as f:
        json.dump({"pages": pages_json}, f, ensure_ascii=False, indent=2)
    with open(export_pkl_path, "wb") as f:
        pickle.dump({"pages": pages_json}, f)
    log(f"[EXPORT] Export global JSON: {export_json_path}")
    log(f"[EXPORT] Export global Pickle: {export_pkl_path}")
    return export_json_path, export_pkl_path

def import_document_json_pickle(json_path=None, pkl_path=None):
    if json_path:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if pkl_path:
        with open(pkl_path, "rb") as f:
            return pickle.load(f)
    return None

def export_lines_to_csv_txt(all_pages_json, export_dir, base_name="lines_extracted"):
    import csv
    lines_csv_path = os.path.join(export_dir, f"{base_name}.csv")
    lines_txt_path = os.path.join(export_dir, f"{base_name}.txt")
    with open(lines_csv_path, "w", newline='', encoding="utf8") as fc, open(lines_txt_path, "w", encoding="utf8") as ft:
        writer = csv.writer(fc)
        writer.writerow(["page_num", "line_num", "text", "bbox"])
        for page in all_pages_json:
            for i, line in enumerate(page.get("lines_extracted", [])):
                writer.writerow([page["page_num"], i+1, line["text"], line["bbox"]])
                ft.write(line["text"].strip() + "\n")
    log(f"[EXPORT] Lignes exportées : {lines_csv_path}, {lines_txt_path}")

def extract_all(
    pdf_path: str,
    max_pages: int = None,
    start_page: int = 1,
    end_page: int = None,
    pages: list = None,
    export_json_pickle: bool = True,
    base_export_name: str = "extraction_doc"
) -> None:
    from tqdm import tqdm
    import pdfplumber

    dirs = make_output_dirs(pdf_path)
    images_dir = dirs["images"]
    tables_dir = dirs["tables"]
    json_dir = dirs["json"]
    mathml_dir = dirs["mathml"]
    htmltables_dir = dirs["htmltables"]
    export_dir = dirs["export"]

    all_pages_json = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        if pages:
            pages_range = [p-1 for p in pages if 1 <= p <= total_pages]
        else:
            start_idx = max(0, start_page - 1)
            end_idx = end_page if end_page is not None else total_pages
            end_idx = min(end_idx, total_pages)
            pages_range = list(range(start_idx, end_idx))
            if max_pages is not None:
                pages_range = pages_range[:max_pages]
        for page_num in tqdm(pages_range, desc="Extraction pages"):
            try:
                log(f"\n[PAGE {page_num+1}] === Extraction début ===")
                page = pdf.pages[page_num]
                img_path = extract_page_image(pdf_path, page_num, images_dir)
                pil_image = Image.open(img_path).convert("RGB")
                features = extract_pdfplumber_features(page, images_dir)
                pdf_words = features["words"]
                ocr_words = extract_words_ocr(img_path)
                existing = set((w["text"], tuple(w["bbox"])) for w in pdf_words)
                for w in ocr_words:
                    if (w["text"], tuple(w["bbox"])) not in existing:
                        pdf_words.append(w)
                features["words"] = pdf_words
                log(f"[FUSION WORDS] pdfplumber={len(pdf_words)}, ocr-only={len(ocr_words)}")

                # CLUSTERING LIGNES (bottom-up)
                lines_extracted = cluster_words_to_lines(features["words"], y_thresh=5)
                features["lines_extracted"] = lines_extracted

                tables = extract_tables(pdf_path, page_num, tables_dir, htmltables_dir)
                blocks_ia = segment_blocks_layoutparser(img_path)
                if not blocks_ia:
                    log("[SEGMENT] Aucun bloc IA détecté, fallback full-page.")
                    blocks_ia = [{
                        "type": "Text",
                        "bbox": [0, 0, pil_image.width, pil_image.height],
                        "score": 1.0,
                        "text": "",
                    }]
                fused_blocks = fusion_blocks(blocks_ia, features, tables, pil_image, mathml_dir)
                page_json = build_page_json(
                    page_num,
                    features.get("page_width"),
                    features.get("page_height"),
                    fused_blocks,
                    logical_structure=None,
                    lines_extracted=lines_extracted
                )
                json_path = os.path.join(json_dir, f"page_{page_num+1}.json")
                with open(json_path, "w", encoding="utf8") as f:
                    json.dump(page_json, f, ensure_ascii=False, indent=2)
                all_pages_json.append(page_json)
                log(f"[SAVE] JSON écrit : {json_path}")
            except Exception as e:
                log(f"[WARN] Extraction skipped for page {page_num+1}: {e}")
                continue
    if export_json_pickle:
        export_document_json_pickle(all_pages_json, export_dir, base_name=base_export_name)
    export_lines_to_csv_txt(all_pages_json, export_dir, base_name="lines_extracted")
    log(f"\nExtraction complète : {json_dir}/page_X.json (et images/tables/formules associés)")
    log(f"Export global JSON/Pickle : {export_dir}/{base_export_name}.json et .pkl")
    log(f"Export lignes CSV/TXT : {export_dir}/lines_extracted.csv et .txt")

# --- Utilisation ---
# extract_all("mon_document.pdf", max_pages=5)

