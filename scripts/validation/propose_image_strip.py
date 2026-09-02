#!/usr/bin/env python3
"""Generuje propozycje mechanicznego usunięcia nawiasowych odniesień '(Image N)' z wyjaśnień."""
import json
import re
import sys
from pathlib import Path

IMG = re.compile(r"\b(image|obraz)\b", re.IGNORECASE)
IMG_PAREN = re.compile(r"\s*\((?:zob\.\s*|por\.\s*)?(?:Image|obraz)[^)]*\)", re.IGNORECASE)


def clean(text):
    out = IMG_PAREN.sub("", text)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([.,;:])", r"\1", out)
    return out.strip()


def main():
    if len(sys.argv) != 3:
        sys.exit("Użycie: propose_image_strip.py <baseline.json> <out-props.json>")
    base = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    props = []
    for q in base["image"]["questions"]:
        cleaned = clean(q["explanation"])
        if IMG.search(cleaned):
            continue  # wplecione w zdanie — Task 4
        props.append({"sheet": q["sheet"], "row": q["row"], "id": q["id"], "field": "Wyjaśnienie", "from": q["explanation"], "to": cleaned,
                      "why": "wyjaśnienie odsyłało do ryciny materiału źródłowego, niewidocznej w quizie", "signals": "mechaniczne usunięcie odniesienia do ryciny"})
    Path(sys.argv[2]).write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"propozycji: {len(props)}")


if __name__ == "__main__":
    main()
