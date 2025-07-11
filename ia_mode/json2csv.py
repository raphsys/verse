# ia_mode/json2csv.py

import os
import json
import csv
from glob import glob

def json_folder_to_csv(json_dir, out_csv):
    rows = []
    json_files = sorted(glob(os.path.join(json_dir, "*.json")))
    for jf in json_files:
        with open(jf, encoding="utf8") as f:
            data = json.load(f)
        page = data.get("page_num", "???")
        for b in data.get("blocks", []):
            for c in b.get("content", []):
                rows.append({
                    "page": page,
                    "block_id": b.get("id"),
                    "block_type": b.get("type"),
                    "phrase": c.get("phrase", ""),
                    "bbox": c.get("bbox", ""),
                    "font": c.get("style", {}),
                    "non_translatable": c.get("non_translatable", False),
                    "is_formula": c.get("is_formula", False),
                    "is_sigle": c.get("is_sigle", False),
                    "has_link": bool(c.get("links", [])),
                })
    with open(out_csv, "w", encoding="utf8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Export CSV prêt : {out_csv}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export CSV des phrases/blocs/styling depuis JSON")
    parser.add_argument("json_dir", help="Dossier des JSON")
    parser.add_argument("--csv", default="export_blocks.csv", help="Chemin CSV de sortie")
    args = parser.parse_args()
    json_folder_to_csv(args.json_dir, args.csv)

