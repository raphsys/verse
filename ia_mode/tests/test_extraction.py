import sys
import os

# Ajoute le dossier parent à sys.path pour importer extraction.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extraction import extract_all

if __name__ == "__main__":
    import argparse

    def parse_pages_list(p):
        if not p:
            return None
        # Accepte : 1,2,3 ou 1-3,5,8 (pages indexées à 1)
        res = []
        for part in p.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                res.extend(list(range(int(start), int(end) + 1)))
            elif part.isdigit():
                res.append(int(part))
        return res if res else None

    parser = argparse.ArgumentParser(
        description="Test pipeline extraction fine ia_mode (par page, plage, ou batch)"
    )
    parser.add_argument("pdf", help="Chemin du PDF à extraire")
    parser.add_argument("--pages", type=str, default=None,
                        help="Pages précises à extraire, ex: 1,3,8 ou 2-5")
    parser.add_argument("--start_page", type=int, default=1, help="Première page à extraire (défaut : 1)")
    parser.add_argument("--end_page", type=int, default=None, help="Dernière page à extraire (défaut: dernière)")
    parser.add_argument("--max_pages", type=int, default=None, help="Nombre max de pages à extraire (défaut: tout)")

    args = parser.parse_args()
    pages_list = parse_pages_list(args.pages)

    extract_all(
        args.pdf,
        max_pages=args.max_pages,
        start_page=args.start_page,
        end_page=args.end_page,
        pages=pages_list
    )

    # Résumé output
    from extraction import make_output_dirs
    dirs = make_output_dirs(args.pdf)
    json_dir = dirs["json"]

    print(f"\nExtraction terminée ! Les JSON sont dans {json_dir}/")
    files = sorted([f for f in os.listdir(json_dir) if f.endswith('.json')])
    if files:
        print(f"\nExemple de contenu du JSON '{files[0]}' :")
        with open(os.path.join(json_dir, files[0]), encoding="utf8") as f:
            import json
            import pprint
            data = json.load(f)
            pprint.pprint(data, compact=True, width=120)
    else:
        print("Aucun fichier JSON généré.")

