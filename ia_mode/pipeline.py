# verse/ia_mode/pipeline.py

import os
from ia_mode.utils import pdf_to_images, save_images
from ia_mode.segment import segment_image
from ia_mode.ocr import ocr_blocks
from ia_mode.translate import translate_blocks
from ia_mode.reconstruct import reconstruct_pdf, reconstruct_docx
from PIL import Image

def extract_figures_from_image(image, blocks, out_dir):
    """
    Pour chaque bloc 'Figure', extrait l'image correspondante et ajoute le chemin dans block['image_path'].
    """
    os.makedirs(out_dir, exist_ok=True)
    for idx, block in enumerate(blocks):
        if block['type'] == 'Figure':
            x1, y1, x2, y2 = block['box']
            cropped = image.crop((x1, y1, x2, y2))
            img_path = os.path.join(out_dir, f"figure_{idx+1}.png")
            cropped.save(img_path)
            block['image_path'] = img_path
    return blocks

def process_pdf(
    pdf_path,
    output_pdf_path="output_translated.pdf",
    output_docx_path=None,
    images_tmp_dir="output_images",
    figures_tmp_dir="output_figures",
    src_lang="fr",
    tgt_lang="en"
):
    # 1. PDF -> images
    print("[1/6] Conversion PDF → images…")
    pages = pdf_to_images(pdf_path, dpi=300, out_dir=images_tmp_dir)
    print(f"    {len(pages)} pages extraites.")
    
    pages_blocks = []
    for i, img in enumerate(pages):
        print(f"[2/6] Segmentation page {i+1}/{len(pages)}…")
        blocs = segment_image(img)
        print(f"    {len(blocs)} blocs détectés.")
        
        print(f"[3/6] Extraction OCR page {i+1}…")
        blocs = ocr_blocks(img, blocs, lang=src_lang)
        
        print(f"[4/6] Traduction automatique page {i+1}…")
        blocs = translate_blocks(blocs, source_lang=src_lang, target_lang=tgt_lang)
        
        print(f"[5/6] Extraction des images (figures) page {i+1}…")
        blocs = extract_figures_from_image(img, blocs, out_dir=figures_tmp_dir)
        
        pages_blocks.append(blocs)

    print("[6/6] Reconstruction PDF final…")
    reconstruct_pdf(pages_blocks, output_pdf_path, images_dir=figures_tmp_dir)
    print(f"PDF multilingue généré : {output_pdf_path}")

    if output_docx_path:
        print("[+] Reconstruction DOCX (optionnel)…")
        reconstruct_docx(pages_blocks, output_docx_path, images_dir=figures_tmp_dir)
        print(f"DOCX multilingue généré : {output_docx_path}")

    print("🎉 Pipeline terminé avec succès !")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline document intelligence PDF multilingue")
    parser.add_argument("pdf", help="Chemin du PDF à traiter")
    parser.add_argument("--pdf_out", default="output_translated.pdf", help="PDF de sortie")
    parser.add_argument("--docx_out", default=None, help="DOCX de sortie (optionnel)")
    parser.add_argument("--src_lang", default="fr", help="Langue source (ex: 'fr')")
    parser.add_argument("--tgt_lang", default="en", help="Langue cible (ex: 'en')")
    args = parser.parse_args()

    process_pdf(
        pdf_path=args.pdf,
        output_pdf_path=args.pdf_out,
        output_docx_path=args.docx_out,
        src_lang=args.src_lang,
        tgt_lang=args.tgt_lang
    )

