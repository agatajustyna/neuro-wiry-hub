#!/usr/bin/env python3
"""Paczki do balansu opcji: unia len15+conj_only+comma_only, grupowana po zbliżonych zestawach stron (group_items), z dossier per paczka."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_dossiers import load_pages  # noqa: E402
from build_question_dossiers import group_items, page_index, render  # noqa: E402


def main():
    if len(sys.argv) != 4:
        sys.exit("Użycie: prepare_balance.py <report.json> <out-dir> <per-group>")
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    seen, qs = set(), []
    for key in ("len15", "conj_only", "comma_only"):
        for q in report["tells"][key]:
            if (q["sheet"], q["row"]) not in seen:
                seen.add((q["sheet"], q["row"]))
                q = dict(q)
                q["tells"] = [k for k in ("len15", "conj_only", "comma_only") if any(x["sheet"] == q["sheet"] and x["row"] == q["row"] for x in report["tells"][k])]
                qs.append(q)
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    per_group = int(sys.argv[3])
    pages = load_pages()
    tf_list, idf = page_index(pages)
    # group_items oczekuje 'options' jako dict — adaptujemy rekordy z measure_tells (options to lista A-D)
    items = [dict(q, options={"A": q["options"][0], "B": q["options"][1], "C": q["options"][2], "D": q["options"][3]}) for q in qs]
    groups = group_items(items, pages, tf_list, idf, per_group=per_group, k=6)
    for i, grp in enumerate(groups):
        batch = []
        for it in grp["items"]:
            rec = {key: v for key, v in it.items() if key != "_pages"}
            rec["options"] = list(rec["options"].values())  # z powrotem lista A-D — format measure_tells, wymagany przez blind_pack i overlay
            batch.append(rec)
        (out / f"batch-{i:02d}.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / f"dossier-{i:02d}.md").write_text(render(pages, grp["pages"]), encoding="utf-8")
    print(f"{len(qs)} pytań -> {len(groups)} paczek w {out}")


if __name__ == "__main__":
    main()
