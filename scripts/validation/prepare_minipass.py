#!/usr/bin/env python3
"""Przygotowuje pakiety mini-pass: poprawna najdłuższa z ratio ≥1.4."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_dossiers import load_pages  # noqa: E402
from build_question_dossiers import group_items, page_index, render  # noqa: E402
from measure_tells import load_questions  # noqa: E402


def main():
    # Load exclusions
    skipped = json.loads(
        Path("docs/validation/detells/skipped-balance.json").read_text(encoding="utf-8")
    )
    skipped_rows = {(s["sheet"], s["row"]) for s in skipped}

    odrzuc_rows = set()
    decisions_dir = Path("docs/validation/detells/adjudicate-balance")
    for dec_file in sorted(decisions_dir.glob("decisions-*.json")):
        batch = json.loads(dec_file.read_text(encoding="utf-8"))
        for dec in batch:
            if dec.get("werdykt") == "ODRZUĆ":
                odrzuc_rows.add((dec["sheet"], dec["row"]))

    excluded = skipped_rows | odrzuc_rows

    # Load questions and select candidates
    questions = load_questions("data/neuro_questions.xlsx")
    selected = []

    for q in questions:
        key = (q["sheet"], q["row"])
        if key in excluded:
            continue

        opts = q.get("options", [])
        if len(opts) < 2:
            continue

        # Get lengths
        lengths = [len(str(o)) for o in opts]
        correct_idx = q.get("correct", -1)
        if correct_idx < 0 or correct_idx >= len(lengths):
            continue

        correct_len = lengths[correct_idx]
        other_lens = [l for i, l in enumerate(lengths) if i != correct_idx]
        second_longest = max(other_lens) if other_lens else 0

        # Check if correct is uniquely longest and ratio ≥ 1.4
        if correct_len > second_longest and correct_len / max(second_longest, 1) >= 1.4:
            rec = dict(q)
            rec["tells"] = ["len_ratio"]
            selected.append(rec)

    # Group into batches with dossiers
    if not selected:
        print("0 pytań -> 0 paczek")
        return

    pages = load_pages()
    tf_list, idf = page_index(pages)

    # Adapt records: options as dict for group_items
    items = [
        dict(rec, options={
            "A": rec["options"][0],
            "B": rec["options"][1],
            "C": rec["options"][2],
            "D": rec["options"][3]
        })
        for rec in selected
    ]

    groups = group_items(items, pages, tf_list, idf, per_group=20, k=6)

    # Write batches
    out_dir = Path("docs/validation/detells/batches-mini")
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, grp in enumerate(groups):
        batch = []
        for it in grp["items"]:
            rec = {key: v for key, v in it.items() if key != "_pages"}
            rec["options"] = list(rec["options"].values())
            batch.append(rec)
        (out_dir / f"batch-{i:02d}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        (out_dir / f"dossier-{i:02d}.md").write_text(
            render(pages, grp["pages"]), encoding="utf-8"
        )

    # Create subdirs
    for subdir in ("results-mini", "verify-mini-input", "verify-mini-key", "verify-mini"):
        (Path("docs/validation/detells") / subdir).mkdir(parents=True, exist_ok=True)

    print(f"{len(selected)} pytań -> {len(groups)} paczek w {out_dir}")


if __name__ == "__main__":
    main()
