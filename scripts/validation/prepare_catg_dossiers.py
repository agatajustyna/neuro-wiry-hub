# -*- coding: utf-8 -*-
"""Buduje dossier per paczka dla Tasku 6 (catg_wrong): unia stron top-k dla każdego
pytania w paczce, wg tf-idf treści pytania + opcji (wzorzec importu jak w
build_question_dossiers.py). Jednorazowy skrypt pomocniczy — brak reużycia poza Task 6.

Użycie: prepare_catg_dossiers.py <batches-dir>
Dla każdego docs/validation/detells/batches-catg/batch-NN.json zapisuje
docs/validation/detells/batches-catg/dossier-NN.md.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_dossiers import load_pages  # noqa: E402
from build_question_dossiers import page_index, top_pages_for, render  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("Użycie: prepare_catg_dossiers.py <batches-dir>")
    batches_dir = sys.argv[1]
    if not os.path.isdir(batches_dir):
        sys.exit(f"BŁĄD: katalog nie istnieje: {batches_dir}")

    batch_files = sorted(glob.glob(os.path.join(batches_dir, "batch-*.json")))
    if not batch_files:
        sys.exit(f"BŁĄD: brak plików batch-*.json w {batches_dir}")

    pages = load_pages()
    if not pages:
        sys.exit("BŁĄD: load_pages() zwróciło pustą listę — sprawdź docs/source-text/")
    tf_list, idf = page_index(pages)

    for bf in batch_files:
        m = re.match(r"batch-(\d+)\.json$", os.path.basename(bf))
        if not m:
            sys.exit(f"BŁĄD: nieoczekiwana nazwa pliku paczki: {bf}")
        nn = m.group(1)

        questions = json.loads(open(bf, encoding="utf-8").read())
        if not questions:
            sys.exit(f"BŁĄD: paczka pusta: {bf}")

        page_union = set()
        for q in questions:
            text = str(q.get("question") or "") + " " + " ".join(str(o or "") for o in (q.get("options") or []))
            page_union |= set(top_pages_for(text, pages, tf_list, idf, k=4))

        idx_list = sorted(page_union)
        if not idx_list:
            sys.exit(f"BŁĄD: brak dopasowanych stron dla paczki {bf}")

        dossier_text = render(pages, idx_list)
        out_path = os.path.join(batches_dir, f"dossier-{nn}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(dossier_text)

        size_kb = os.path.getsize(out_path) / 1024
        print(f"batch-{nn}: {len(questions)} pytań -> {len(idx_list)} stron, dossier-{nn}.md ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
