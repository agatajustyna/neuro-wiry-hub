#!/usr/bin/env python3
"""Zaślepione wejście dla ślepego solvera: bez klucza, opcje przetasowane deterministycznie (permutacje w osobnym pliku)."""
import json
import random
import sys
from pathlib import Path


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit("Użycie: blind_pack.py <records.json> <out-blind.json> <out-key.json> [sample-N]")
    records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not records:
        sys.exit("BŁĄD: pusta lista rekordów")
    if len(sys.argv) == 5:
        records = random.Random("sample-detells").sample(records, min(int(sys.argv[4]), len(records)))
    blind, key = [], []
    for q in records:
        perm = [0, 1, 2, 3]
        random.Random(f"{q['sheet']}:{q['row']}").shuffle(perm)
        blind.append({"sheet": q["sheet"], "row": q["row"], "id": q["id"], "question": q["question"], "options": [q["options"][j] for j in perm]})
        key.append({"sheet": q["sheet"], "row": q["row"], "perm": perm, "correct_blind_index": perm.index(q["correct"])})
    Path(sys.argv[2]).write_text(json.dumps(blind, ensure_ascii=False, indent=1), encoding="utf-8")
    Path(sys.argv[3]).write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pytań: {len(blind)}")


if __name__ == "__main__":
    main()
