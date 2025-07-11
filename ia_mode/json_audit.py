# ia_mode/json_audit.py

import os
import json
import argparse
from collections import Counter, defaultdict
from glob import glob

def audit_json_folder(json_dir):
    json_files = sorted(glob(os.path.join(json_dir, "*.json")))
    global_stats = Counter()
    type_stats = defaultdict(Counter)
    warnings = []

    for jf in json_files:
        with open(jf, encoding="utf8") as f:
            data = json.load(f)
        page = data.get("page_num", "???")
        blocks = data.get("blocks", [])
        global_stats["pages"] += 1
        global_stats["blocks"] += len(blocks)

        types_on_page = Counter()
        for b in blocks:
            btype = b.get("type", "Unknown")
            types_on_page[btype] += 1
            type_stats[btype]["count"] += 1
            if not b.get("bbox") or not isinstance(b.get("bbox"), list):
                warnings.append(f"Page {page} - Bloc {b['id']} : bbox manquant ou incorrect")
            if not b.get("sentences"):
                warnings.append(f"Page {page} - Bloc {b['id']} : pas de phrase extraite")
            if btype == "Table" and not b.get("tables"):
                warnings.append(f"Page {page} - Bloc {b['id']} : Table sans data")
        print(f"Page {page} : {len(blocks)} blocs ({dict(types_on_page)})")

    print("\nRésumé global :")
    print(f"  Pages analysées : {global_stats['pages']}")
    print(f"  Total blocs     : {global_stats['blocks']}")
    print("  Répartition par type :")
    for t, s in type_stats.items():
        print(f"    {t:<12} : {s['count']}")
    print("\nWarnings/Anomalies :")
    for w in warnings:
        print("  -", w)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit structure et statistiques JSON extractions WYSIWYG")
    parser.add_argument("json_dir", help="Dossier contenant les JSON extraits")
    args = parser.parse_args()
    audit_json_folder(args.json_dir)

