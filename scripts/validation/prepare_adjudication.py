#!/usr/bin/env python3
"""Buduje pakiety do adjudykacji z trzech źródeł: spory, zablokowane, odroczenia z Task 6."""
import json
import sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_dossiers import load_pages  # noqa: E402
from build_question_dossiers import page_index, top_pages_for  # noqa: E402
from measure_tells import load_questions  # noqa: E402


def main():
    # Load input files
    disputes = json.loads(
        Path("docs/validation/detells/disputes-balance.json").read_text(encoding="utf-8")
    )
    blocked_raw = json.loads(
        Path("docs/validation/detells/blocked-balance.json").read_text(encoding="utf-8")
    )
    deferred = json.loads(
        Path("docs/validation/detells/deferred-catg.json").read_text(encoding="utf-8")
    )

    # Convert blocked record to prop
    props_all = list(disputes)
    for blocked in blocked_raw:
        # Adapt the blocked record: keep current_value and apply intended change
        prop = {
            "sheet": blocked["sheet"],
            "row": blocked["row"],
            "id": blocked["id"],
            "field": blocked["field"],
            "from": blocked["current_value"],
            "to": blocked["proposed_to"],
            "why": "Zmiana zaproponowana przez edytora (konflikt: bieżąca wartość różniła się od oczekiwanej)",
            "signals": "balans opcji (adaptacja po konflikcie)"
        }
        props_all.append(prop)

    # Add deferred
    props_all.extend(deferred)

    # Load current question state and pages
    questions = load_questions("data/neuro_questions.xlsx")
    q_map = {(q["sheet"], q["row"]): q for q in questions}
    pages = load_pages()
    tf_list, idf = page_index(pages)

    # Load verify context (solver answers and kontroler verdicts)
    verify_balance_dir = Path("docs/validation/detells/verify-balance")
    verify_catg_dir = Path("docs/validation/detells") / "verify-catg"
    verify_key_dir = Path("docs/validation/detells/verify-key")
    batches_dir = Path("docs/validation/detells/batches-balance")

    solver_answers = {}  # (sheet, row) -> answer_index
    verdicts = {}  # (sheet, row) -> list of {uzasadnienie}

    # Load verify-balance
    for solver_file in verify_balance_dir.glob("solver-batch-*.json"):
        batch = json.loads(solver_file.read_text(encoding="utf-8"))
        for rec in batch:
            solver_answers[(rec["sheet"], rec["row"])] = rec.get("answer_index")

    for kontroler_file in verify_balance_dir.glob("kontroler-batch-*.json"):
        batch = json.loads(kontroler_file.read_text(encoding="utf-8"))
        for rec in batch:
            key = (rec["sheet"], rec["row"])
            if key not in verdicts:
                verdicts[key] = []
            if rec.get("werdykt") != "CZYSTO":
                verdicts[key].append(rec.get("uzasadnienie", ""))

    # Try to load verify-catg if exists
    if verify_catg_dir.exists():
        for solver_file in verify_catg_dir.glob("solver-*.json"):
            batch = json.loads(solver_file.read_text(encoding="utf-8"))
            for rec in batch:
                solver_answers[(rec["sheet"], rec["row"])] = rec.get("answer_index")
        for kontroler_file in verify_catg_dir.glob("kontroler-*.json"):
            batch = json.loads(kontroler_file.read_text(encoding="utf-8"))
            for rec in batch:
                key = (rec["sheet"], rec["row"])
                if key not in verdicts:
                    verdicts[key] = []
                if rec.get("werdykt") != "CZYSTO":
                    verdicts[key].append(rec.get("uzasadnienie", ""))

    # Load keys to find solver misses
    keys = {}  # (sheet, row) -> correct_blind_index
    for key_file in verify_key_dir.glob("batch-*.json"):
        batch = json.loads(key_file.read_text(encoding="utf-8"))
        for rec in batch:
            keys[(rec["sheet"], rec["row"])] = rec.get("correct_blind_index")

    # Group props by row, compute context and pages
    rows_to_adjudicate = {}  # (sheet, row) -> {props: [...], context: {...}, pages: {...}}

    for prop in props_all:
        key = (prop["sheet"], prop["row"])
        if key not in rows_to_adjudicate:
            q = q_map.get(key)
            if not q:
                print(f"WARNING: Question not found: {key}", file=sys.stderr)
                continue

            # Compute solver context
            solver_answer = solver_answers.get(key)
            correct_idx = keys.get(key)
            solver_miss = solver_answer != correct_idx
            solver_picked_text = ""
            if solver_miss and solver_answer is not None and 0 <= solver_answer < 4:
                if "options" in q:
                    opts = q["options"]
                    if isinstance(opts, list) and len(opts) > solver_answer:
                        solver_picked_text = opts[solver_answer]

            context = {
                "solver_miss": solver_miss,
                "solver_picked_text": solver_picked_text,
                "zastrzezenia": verdicts.get(key, [])
            }

            # Compute top pages
            q_text = (q.get("question") or "") + " " + " ".join(q.get("options") or [])
            top_pgs = top_pages_for(q_text, pages, tf_list, idf, k=3)
            book_pages = sorted(set(pages[i]["book"] for i in top_pgs if i < len(pages)))
            pdf_pages = sorted(set(pages[i]["pdf"] for i in top_pgs if i < len(pages)))

            rows_to_adjudicate[key] = {
                "question": q,
                "props": [],
                "context": context,
                "book_pages": book_pages,
                "pdf_pages": pdf_pages
            }

        rows_to_adjudicate[key]["props"].append(prop)

    # Group rows into packets by PDF pages union
    packets = []
    remaining_rows = list(rows_to_adjudicate.items())

    while remaining_rows:
        packet_rows = []
        packet_pdf_pages = set()

        # Greedy: add rows while union <= 12
        i = 0
        while i < len(remaining_rows):
            key, data = remaining_rows[i]
            new_pages = set(data["pdf_pages"])
            union = packet_pdf_pages | new_pages
            if len(union) <= 12 or not packet_rows:  # Always add first row
                packet_rows.append((key, data))
                packet_pdf_pages = union
                remaining_rows.pop(i)
            else:
                i += 1

        # Build packet
        packet = {
            "pdf_pages": sorted(packet_pdf_pages),
            "book_pages": sorted(set(
                p for _, data in packet_rows for p in data["book_pages"]
            )),
            "rows": [{
                "sheet": key[0],
                "row": key[1],
                "id": data["question"].get("id"),
                "question": data["question"].get("question"),
                "options": data["question"].get("options"),
                "correct": data["question"].get("correct"),
                "explanation": data["question"].get("explanation"),
                "props": data["props"],
                "context": data["context"]
            } for key, data in packet_rows]
        }
        packets.append(packet)

    # Write packets
    out_dir = Path("docs/validation/detells/adjudicate-balance")
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, pkt in enumerate(packets):
        (out_dir / f"packet-{i:02d}.json").write_text(
            json.dumps(pkt, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    # Report
    total_rows = sum(len(pkt["rows"]) for pkt in packets)
    print(f"{len(packets)} pakietów, {total_rows} wierszy total")
    for i, pkt in enumerate(packets):
        max_pdf = max(pkt["pdf_pages"]) if pkt["pdf_pages"] else 0
        print(
            f"  packet-{i:02d}: {len(pkt['rows'])} rows, "
            f"{len(pkt['pdf_pages'])} PDF pages (max {max_pdf})"
        )


if __name__ == "__main__":
    main()
