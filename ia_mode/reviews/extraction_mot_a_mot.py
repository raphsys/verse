import os
import json
import re
import camelot
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import spacy

import layoutparser as lp
from typing import List, Dict, Any, Tuple

from lxml import etree

DEBUG = True
def log(msg):
    if DEBUG: print(msg)

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
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs

def infer_style(word: dict) -> dict:
    return {
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

def detect_alignment(block_words: List[dict], block_bbox: List[float]) -> str:
    if not block_words: return "unknown"
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
        for i, w in enumerate(words):
            style = infer_style(w)
            result["words"].append({
                "id": i,
                "text": w.get("text", ""),
                "bbox": [w.get('x0', 0), w.get('top', 0), w.get('x1', 0), w.get('bottom', 0)],
                "style": style
            })
    except Exception as e:
        log(f"[WARN] extract_words failed: {e}")
    # ... (lines, hyperlinks, images idem, tu peux garder)
    return result

def group_words_by_block(words, block_bbox):
    return [w for w in words if
            block_bbox[0] <= w["bbox"][0] <= block_bbox[2] and
            block_bbox[1] <= w["bbox"][1] <= block_bbox[3]]

def merge_vertical_blocks(blocks: List[Dict[str, Any]], thresh: float = 15.0) -> List[Dict[str, Any]]:
    merged = []
    used = [False] * len(blocks)
    for i, blk in enumerate(blocks):
        if used[i]: continue
        curr = blk.copy()
        for j, other in enumerate(blocks):
            if i == j or used[j]: continue
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
    return blocks

def fusion_blocks(
    blocks_ia: List[Dict[str, Any]],
    features_classic: Dict[str, Any],
    tables: List[Dict[str, Any]],
    image: Image.Image
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    fused_blocks = []
    all_words = features_classic.get("words", [])
    for block_id, block in enumerate(blocks_ia):
        block_words = group_words_by_block(all_words, block["bbox"])
        word_ids = [w["id"] for w in block_words]
        block_json = {
            "id": block_id,
            "type": block.get("type", ""),
            "bbox": block.get("bbox", [0,0,0,0]),
            "score": block.get("score", 1.0),
            "word_ids": word_ids,
        }
        fused_blocks.append(block_json)
    log(f"[FUSION] => {len(fused_blocks)} blocs fusionnés sur la page.")
    return fused_blocks, all_words

def build_page_json(page_num: int, width: int, height: int, fused_blocks: List[Dict[str, Any]], all_words: List[Dict[str, Any]], logical_structure: Any = None) -> Dict[str, Any]:
    return {
        "page_num": page_num + 1,
        "width": width,
        "height": height,
        "blocks": fused_blocks,
        "words": all_words,
        "logical_structure": logical_structure or []
    }

def extract_all(
    pdf_path: str,
    max_pages: int = None,
    start_page: int = 1,
    end_page: int = None,
    pages: list = None
) -> None:
    from tqdm import tqdm
    import pdfplumber

    dirs = make_output_dirs(pdf_path)
    images_dir = dirs["images"]
    tables_dir = dirs["tables"]
    json_dir = dirs["json"]
    htmltables_dir = dirs["htmltables"]

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
                fused_blocks, all_words = fusion_blocks(blocks_ia, features, tables, pil_image)
                page_json = build_page_json(page_num, features.get("page_width"), features.get("page_height"), fused_blocks, all_words)
                json_path = os.path.join(json_dir, f"page_{page_num+1}.json")
                with open(json_path, "w", encoding="utf8") as f:
                    json.dump(page_json, f, ensure_ascii=False, indent=2)
                log(f"[SAVE] JSON écrit : {json_path}")
            except Exception as e:
                log(f"[WARN] Extraction skipped for page {page_num+1}: {e}")
                continue
    log(f"\nExtraction complète : {json_dir}/page_X.json (et images/tables associés)")

