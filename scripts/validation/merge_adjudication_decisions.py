#!/usr/bin/env python3
"""Łączy decyzje adjudykatorów w props-adjudicated.json."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure_tells import load_questions  # noqa: E402

FIELD_COL = {"ID": 1, "Pytanie": 2, "A": 3, "B": 4, "C": 5, "D": 6, "Poprawna": 7, "Wyjaśnienie": 8}
LETTER_TO_FIELD = {"A": 0, "B": 1, "C": 2, "D": 3}


def get_current_value(questions, sheet, row, field):
    """Get current cell value from xlsx."""
    for q in questions:
        if q["sheet"] == sheet and q["row"] == row:
            if field in LETTER_TO_FIELD:
                idx = LETTER_TO_FIELD[field]
                opts = q.get("options", [])
                if idx < len(opts):
                    return opts[idx]
            else:
                return q.get(field.lower().replace("wyjaśnienie", "explanation"), "")
    return None


def main():
    # Load current state
    questions = load_questions("data/neuro_questions.xlsx")

    # Load all decisions
    decisions_dir = Path("docs/validation/detells/adjudicate-balance")
    all_decisions = []
    for dec_file in sorted(decisions_dir.glob("decisions-*.json")):
        batch = json.loads(dec_file.read_text(encoding="utf-8"))
        all_decisions.extend(batch)

    # Process decisions
    props = []
    applied = 0
    rejected = 0
    already_applied = 0

    for dec in all_decisions:
        werdykt = dec.get("werdykt")

        if werdykt == "ODRZUĆ":
            rejected += 1
            continue

        if werdykt not in ("PRZYJMIJ", "KOREKTA"):
            print(f"WARNING: unknown werdykt '{werdykt}'", file=sys.stderr)
            continue

        # Get current value
        to_final = dec.get("to_final")
        if to_final is None:
            print(
                f"ERROR: {dec['sheet']} w.{dec['row']} [{dec['field']}]: "
                f"to_final is None",
                file=sys.stderr
            )
            continue

        current = get_current_value(questions, dec["sheet"], dec["row"], dec["field"])
        if current is None:
            print(
                f"ERROR: {dec['sheet']} w.{dec['row']} [{dec['field']}]: "
                f"current value not found",
                file=sys.stderr
            )
            continue

        # Check if already applied
        if str(current) == str(to_final):
            already_applied += 1
            print(f"POMINIĘTO (już naniesione): {dec['sheet']} w.{dec['row']} [{dec['field']}]")
            continue

        # Build prop
        prop = {
            "sheet": dec["sheet"],
            "row": dec["row"],
            "id": dec["id"],
            "field": dec["field"],
            "from": current,
            "to": to_final,
            "why": dec.get("why", ""),
            "signals": dec.get("signals", "")
        }
        props.append(prop)
        applied += 1

    Path("docs/validation/detells/props-adjudicated.json").write_text(
        json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(
        f"PRZYJMIJ/KOREKTA: {applied} propozycji, ODRZUĆ: {rejected}, "
        f"już naniesione: {already_applied}"
    )


if __name__ == "__main__":
    main()
