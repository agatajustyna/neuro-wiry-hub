#!/usr/bin/env python3
"""Dzieli pytania z raportu measure_tells na paczki dla agentów LLM."""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 5:
        sys.exit("Użycie: prepare_batches.py <report.json> <image|paren_only|comma_only|catg_wrong|len15|conj_only> <out-dir> <batch-size>")
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    key = sys.argv[2]
    qs = report["image"]["questions"] if key == "image" else report["tells"][key]
    if not qs:
        sys.exit(f"BŁĄD: brak pytań dla klucza '{key}'")
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    size = int(sys.argv[4])
    for i in range(0, len(qs), size):
        (out / f"batch-{i // size:02d}.json").write_text(json.dumps(qs[i:i + size], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(qs)} pytań -> {(len(qs) + size - 1) // size} paczek w {out}")


if __name__ == "__main__":
    main()
