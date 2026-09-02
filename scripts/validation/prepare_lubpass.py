#!/usr/bin/env python3
"""Przygotowuje pakiety domykające dla wyróżnika 'lub' tylko-w-poprawnej (one-off)."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_dossiers import load_pages  # noqa: E402
from build_question_dossiers import group_items, page_index, render  # noqa: E402
from measure_tells import load_questions, only_correct  # noqa: E402

LUB = re.compile(r"\blub\b", re.IGNORECASE)


def main():
    questions = load_questions("data/neuro_questions.xlsx")
    selected_qs = only_correct(questions, LUB)
    if not selected_qs:
        sys.exit("BŁĄD: brak pytań z 'lub' tylko-w-poprawnej")

    selected = []
    for q in selected_qs:
        rec = dict(q)
        rec["tells"] = ["lub_only"]
        selected.append(rec)

    pages = load_pages()
    tf_list, idf = page_index(pages)

    items = [
        dict(rec, options={"A": rec["options"][0], "B": rec["options"][1], "C": rec["options"][2], "D": rec["options"][3]})
        for rec in selected
    ]

    groups = group_items(items, pages, tf_list, idf, per_group=13, k=6)

    out_dir = Path("docs/validation/detells/batches-lub")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, grp in enumerate(groups):
        batch = []
        for it in grp["items"]:
            rec = {key: v for key, v in it.items() if key != "_pages"}
            rec["options"] = list(rec["options"].values())
            batch.append(rec)
        (out_dir / f"batch-{i:02d}.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / f"dossier-{i:02d}.md").write_text(render(pages, grp["pages"]), encoding="utf-8")

    for subdir in ("results-lub", "verify-lub-input", "verify-lub-key", "verify-lub"):
        (Path("docs/validation/detells") / subdir).mkdir(parents=True, exist_ok=True)

    print(f"{len(selected)} pytań -> {len(groups)} paczek w {out_dir}")


if __name__ == "__main__":
    main()
