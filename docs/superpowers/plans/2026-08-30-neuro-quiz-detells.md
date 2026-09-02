# Usunięcie odniesień „Image" i wyróżników zdradzających odpowiedź — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** W `data/neuro_questions.xlsx` usunąć 321 odniesień do „Image N" z wyjaśnień oraz zredukować o ≥90% wyróżniki pozwalające zgadnąć poprawną odpowiedź bez wiedzy (1182 pytania), z pełnym logiem zmian i weryfikacją merytoryczną.

**Architecture:** Każdy przebieg produkuje plik propozycji zmian (JSON w formacie dziennika), a jeden wspólny, walidujący applier nanosi je na xlsx i dopisuje do `docs/validation/applied-changes.json`. Przebiegi mechaniczne działają lokalnie w Pythonie; przebiegi wymagające osądu wykonują agenci LLM na paczkach plików z dysku, z dossier tekstowym z transkrypcji podręcznika. Zmiany treści dystraktorów przechodzą przez niezależną weryfikację (ślepy solver + kontroler błędności), spory rozstrzyga rozjemca na skanie grupowanym po stronach.

**Tech Stack:** Python 3 + openpyxl (skrypty w `scripts/validation/`), agenci LLM (Sonnet do masówki, model najmocniejszy tylko do rozjemstwa), pytest, vitest.

**Spec:** Uzgodnienia z rozmowy 2026-08-30 (pomiar skali: sekcja „Baseline" niżej). Metodyka i lekcje: `scripts/validation/README.md`, `docs/validation/STATUS.md`, `docs/validation/DECISIONS.md`.

## Global Constraints

- Poprawki idą do `data/neuro_questions.xlsx`, NIGDY do wygenerowanych JSON-ów w `public/data/`.
- Każda zmiana w xlsx = wpis w `docs/validation/applied-changes.json` w schemacie `{sheet, row, id, field, from, to, why, signals}`; `field` ∈ {`Pytanie`, `A`, `B`, `C`, `D`, `Poprawna`, `Wyjaśnienie`, `Wykluczone`, `ID`}.
- Agenci NIE czytają skanu PDF. Wyłącznie dossier tekstowe z `docs/source-text/` (transkrypcja, 18 plików, nagłówki `## [PDF <n> | str. książki <m>]`; przelicznik: strona PDF = strona książki − 3). Skan tylko w rozjemstwie, grupowany po stronach.
- Agent zapisuje wynik na dysk w trakcie pracy, zanim go zwróci; do agenta idą ŚCIEŻKI plików paczek, nie ich treść.
- Brakujący parametr/plik = twardy błąd skryptu (`sys.exit`), nigdy wartość domyślna ani fallback.
- Wyjaśnienia nie mogą cytować liter odpowiedzi (aplikacja tasuje opcje; wzorzec kontrolny jak `cites_letter()` w `scripts/generate_quiz_data.py`).
- Po edycji dowolnej opcji obowiązkowe sprawdzenie, czy wyjaśnienie nie broni usuniętej/zmienionej treści.
- Edytowany dystraktor musi POZOSTAĆ błędny — potwierdzenie względem dossier, nie „na oko". Detektory leksykalne (dopasowanie słów) zawodzą po polsku — kryteria weryfikacji mają być obiektywne (klucz nienaruszony, cytat z dossier przy każdej zmianie treści).
- Pliki robocze przebiegów: `docs/validation/detells/` (katalog jest w `.gitignore` — publiczne repo nie może nieść cytatów z podręcznika). Paczki tymczasowe: scratchpad sesji.
- Repo publiczne: NIGDY `git push --all` (lokalna gałąź `develop-full` niesie chronioną historię).
- Praca na gałęzi `detells` w forku `adamdrzewiecki/neuro-wiry-hub`; push po SSH; PR do `agatajustyna/neuro-wiry-hub` dopiero po potwierdzeniu przez użytkownika.
- Kolumny arkusza pytań: 1=ID, 2=Pytanie, 3–6=A–D, 7=Poprawna, 8=Wyjaśnienie, 9=Tagi, 10=Wykluczone. Wiersze wykluczone (`Wykluczone=TAK`), nagłówkowe i separatory pomijamy — filtr identyczny jak w `generate_quiz_data.py`.
- Limit linii kodu: 200 znaków. Treści po polsku, z pełnymi znakami diakrytycznymi.

## Baseline (pomiar z 2026-08-30, xlsx @ commit 75e1503)

- Pytań w quizie: 3355. Odniesień „Image": 321 pytań, wyłącznie pole Wyjaśnienie (141 czysto nawiasowych, 180 wplecionych w zdanie), 26 unikalnych numerów rycin, skupione w działach 9–10.
- Wyróżniki (unia 1182 pytań, 35,2%): poprawna ≥1,5× najdłuższa — 855; koniunkcja „i/oraz" tylko w poprawnej — 383; nawias tylko w poprawnej — 359; przecinek tylko w poprawnej — 93; zwroty kategoryczne w ≥2 błędnych przy czystej poprawnej — 99. Poprawna najdłuższa w 54,5% pytań (los ~25%), najkrótsza w 8,5% (w tym silnie — ≤0,67× drugiej najkrótszej — 1,5%). Token „lub": 32× w poprawnych vs 1× w błędnych.

## Cele akceptacyjne (Task 8)

| Metryka | Baseline | Cel |
|---|---|---|
| odniesienia do rycin (wszystkie pola) | 321 | **0** |
| nawias tylko-w-poprawnej | 359 | ≤ 36 |
| koniunkcja tylko-w-poprawnej | 383 | ≤ 40 |
| przecinek tylko-w-poprawnej | 93 | ≤ 10 |
| kategoryczne w ≥2 błędnych | 99 | ≤ 10 |
| poprawna ≥1,5× najdłuższa | 855 | ≤ 170 (5%) |
| poprawna najdłuższa (unikatowo) | 54,5% | ≤ 35% |
| poprawna najkrótsza (unikatowo) — strażnik regresji | 8,5% (silnie: 1,5%) | ≤ 12% (silnie ≤ 3%) |

Strażnik „najkrótszej" pilnuje, żeby skracanie poprawnych opcji (Taski 5 i 7) nie wyprodukowało tella odwrotnego — to założenie kierunkowe (skala ryzyka niezmierzona), stąd próg tolerancyjny zamiast celu redukcji.

---

### Task 1: Instrument pomiarowy `measure_tells.py` + gałąź robocza

**Files:**
- Create: `scripts/validation/measure_tells.py`
- Test: uruchomienie na bieżącym xlsx z porównaniem do baseline

**Interfaces:**
- Produces: `python3 scripts/validation/measure_tells.py <xlsx> <out.json>` — stdout: podsumowanie; `<out.json>`: `{"n": int, "image": {"total": int, "parenthetical": int, "embedded": int, "questions": [{"sheet","row","id","explanation"}]}, "tells": {"conj_only": [...], "paren_only": [...], "comma_only": [...], "catg_wrong": [...], "len15": [...]}, "union": [["sheet", row], ...]}` — listy pytań w tym samym formacie co `image.questions`, plus pola `question`, `options`, `correct`.

- [ ] **Step 1: Gałąź robocza**

```bash
cd /Users/adamdrzewiecki/IntelliJProjects/private/neuro_quiz/neuro-wiry-hub
git checkout -b detells
mkdir -p docs/validation/detells
```

- [ ] **Step 2: Napisz `scripts/validation/measure_tells.py`**

Definicje (dokładnie te — akceptacja jest na nich liczona):

```python
#!/usr/bin/env python3
"""Pomiar odniesień do rycin i wyróżników zdradzających odpowiedź. Instrument akceptacyjny planu detells."""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate_quiz_data import cell_text, is_excluded  # noqa: E402

LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
IMG = re.compile(r"\bimage\b", re.IGNORECASE)
IMG_PAREN = re.compile(r"\s*\((?:zob\.\s*|por\.\s*)?Image[^)]*\)", re.IGNORECASE)
CONJ = re.compile(r"\S\s+(i|oraz)\s+\S", re.IGNORECASE)
PAREN = re.compile(r"\([^)]{3,}\)")
COMMA = re.compile(r",")
CATG = re.compile(r"\b(tylko|wyłącznie|nigdy|zawsze|jedynie|każd\w+|wszystk\w+|żad\w+)\b", re.IGNORECASE)


def load_questions(xlsx_path):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_path)
    out = []
    for sheet in [s for s in wb.sheetnames if s != "Struktura"]:
        ws = wb[sheet]
        for row in range(2, ws.max_row + 1):
            vals = [cell_text(ws.cell(row, c)) for c in range(1, 11)]
            qid, q, a, b, c_, d, correct, expl, _tags, excl = vals
            if q == "Pytanie" and a == "A":
                continue
            if q and not any([a, b, c_, d]):
                continue
            if is_excluded(excl):
                continue
            if not all([q, a, b, c_, d]):
                continue
            ci = LETTER_TO_INDEX.get(correct.strip().upper()[:1] if correct else "")
            if ci is None:
                continue
            out.append({"sheet": sheet, "row": row, "id": qid, "question": q, "options": [a, b, c_, d], "correct": ci, "explanation": expl})
    return out


def only_correct(qs, pat):
    hits = []
    for q in qs:
        flags = [bool(pat.search(o)) for o in q["options"]]
        if flags[q["correct"]] and sum(flags) == 1:
            hits.append(q)
    return hits


def main():
    if len(sys.argv) != 3:
        sys.exit("Użycie: measure_tells.py <xlsx> <out.json>")
    qs = load_questions(sys.argv[1])
    n = len(qs)
    img_qs = [q for q in qs if IMG.search(q["explanation"])]
    par = sum(1 for q in img_qs if not IMG.search(IMG_PAREN.sub("", q["explanation"])))
    catg_wrong, len15, longest, shortest, strong_shortest = [], [], 0, 0, 0
    tok_c, tok_w = collections.Counter(), collections.Counter()
    for q in qs:
        flags = [bool(CATG.search(o)) for o in q["options"]]
        if not flags[q["correct"]] and sum(flags) >= 2:
            catg_wrong.append(q)
        lens = [len(o) for o in q["options"]]
        mx, mn = max(lens), min(lens)
        if lens[q["correct"]] == mx and lens.count(mx) == 1:
            longest += 1
            if lens[q["correct"]] >= 1.5 * sorted(lens, reverse=True)[1]:
                len15.append(q)
        if lens[q["correct"]] == mn and lens.count(mn) == 1:
            shortest += 1
            if lens[q["correct"]] <= 0.67 * sorted(lens)[1]:
                strong_shortest += 1
        for i, o in enumerate(q["options"]):
            (tok_c if i == q["correct"] else tok_w).update(set(re.findall(r"[a-ząćęłńóśźż]{3,}", o.lower())))
    token_ratios = sorted(((round(cc / max(tok_w.get(t, 0) / 3, 0.5), 1), cc, tok_w.get(t, 0), t) for t, cc in tok_c.items() if cc >= 20 and cc / max(tok_w.get(t, 0) / 3, 0.5) >= 2), reverse=True)
    tells = {"conj_only": only_correct(qs, CONJ), "paren_only": only_correct(qs, PAREN), "comma_only": only_correct(qs, COMMA), "catg_wrong": catg_wrong, "len15": len15}
    union = sorted({(q["sheet"], q["row"]) for lst in tells.values() for q in lst})
    report = {"n": n, "image": {"total": len(img_qs), "parenthetical": par, "embedded": len(img_qs) - par, "questions": img_qs}, "tells": tells, "union": [list(u) for u in union],
              "length": {"longest": longest, "shortest": shortest, "strong_shortest": strong_shortest},
              "token_ratios": [{"token": t, "ratio": r, "correct": cc, "wrong": wc} for r, cc, wc, t in token_ratios]}
    Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pytań: {n} | image: {len(img_qs)} (nawiasowe {par}, wplecione {len(img_qs) - par})")
    for k, v in tells.items():
        print(f"{k}: {len(v)}")
    print(f"poprawna najdłuższa: {longest} ({100 * longest / n:.1f}%) | najkrótsza: {shortest} ({100 * shortest / n:.1f}%), w tym silnie: {strong_shortest} ({100 * strong_shortest / n:.1f}%) | unia: {len(union)} ({100 * len(union) / n:.1f}%)")
    print("tokeny ratio>=2 (top 5): " + ", ".join(f"{t} {r}" for r, cc, wc, t in token_ratios[:5]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Uruchom i porównaj z baseline**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/baseline.json`
Expected: `pytań: 3355 | image: 321 (nawiasowe 141, wplecione 180)`, `conj_only: 383`, `paren_only: 359`, `comma_only: 93`, `catg_wrong: 99`, `len15: 855`, `poprawna najdłuższa: 1829 (54.5%) | najkrótsza: 285 (8.5%), w tym silnie: 49 (1.5%) | unia: 1182 (35.2%)`, `tokeny ratio>=2 (top 5): lub 64.0, hipokampa 4.6, między 4.0, bruzdy 3.8, bocznym 3.5`. Rozjazd o >2 przy dowolnej metryce = STOP, wyjaśnić przyczynę przed dalszą pracą.

- [ ] **Step 4: Commit**

```bash
git add scripts/validation/measure_tells.py
git commit -m "feat: add measure_tells.py — instrument pomiaru wyróżników odpowiedzi"
```

---

### Task 2: Walidujący applier `apply_field_changes.py`

**Files:**
- Create: `scripts/validation/apply_field_changes.py`
- Test: `scripts/validation/test_apply_field_changes.py` (pytest, syntetyczny xlsx w tmp_path)

**Interfaces:**
- Consumes: plik propozycji JSON — lista `{sheet, row, id, field, from, to, why, signals}` (dokładnie schemat dziennika).
- Produces: `python3 scripts/validation/apply_field_changes.py <xlsx> <proposals.json> [--apply]` — bez `--apply` tylko raportuje (dry-run). Z `--apply`: nanosi na xlsx i DOPISUJE wpisy do `docs/validation/applied-changes.json`. Powtórne uruchomienie tych samych propozycji jest bezpieczne (już naniesione są pomijane, dziennik nie dubluje wpisów). Używany przez Taski 3–7.

- [ ] **Step 0: Zainstaluj pytest**

Systemowy Python 3.9 nie ma pytest (zweryfikowane: `python3 -m pytest` → `No module named pytest`; pip 21.2.4 dostępny).

Run: `python3 -m pip install --user pytest`
Potem: `python3 -m pytest --version` — Expected: wypisana wersja.

- [ ] **Step 1: Napisz test (pytest)**

```python
# scripts/validation/test_apply_field_changes.py
import json
import subprocess
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
FIELD_COL = {"ID": 1, "Pytanie": 2, "A": 3, "B": 4, "C": 5, "D": 6, "Poprawna": 7, "Wyjaśnienie": 8, "Wykluczone": 10}


def make_xlsx(path):
    wb = openpyxl.Workbook()
    wb.active.title = "Struktura"
    ws = wb.create_sheet("1.Testowy")
    ws.append(["ID", "Pytanie", "A", "B", "C", "D", "Poprawna", "Wyjaśnienie", "Tagi", "Wykluczone"])
    ws.append(["T-1", "Co?", "a1", "b1", "c1", "d1", "A", "Bo tak (Image 5).", "", ""])
    wb.save(path)


def run(xlsx, proposals, log, apply=False):
    cmd = [sys.executable, str(HERE / "apply_field_changes.py"), str(xlsx), str(proposals), "--log", str(log)]
    if apply:
        cmd.append("--apply")
    return subprocess.run(cmd, capture_output=True, text=True)


def test_apply_and_log(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-1", "field": "Wyjaśnienie", "from": "Bo tak (Image 5).", "to": "Bo tak.", "why": "usunięcie odniesienia do ryciny", "signals": "test"}]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = run(xlsx, p, log, apply=True)
    assert r.returncode == 0, r.stderr
    ws = openpyxl.load_workbook(xlsx)["1.Testowy"]
    assert ws.cell(2, FIELD_COL["Wyjaśnienie"]).value == "Bo tak."
    assert len(json.loads(log.read_text(encoding="utf-8"))) == 1


def test_stale_from_fails(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-1", "field": "Wyjaśnienie", "from": "INNA TREŚĆ", "to": "X.", "why": "w", "signals": "test"}]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = run(xlsx, p, log, apply=True)
    assert r.returncode != 0
    assert "INNA TREŚĆ"[:4] in r.stderr or "from" in r.stderr


def test_id_mismatch_fails(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-99", "field": "A", "from": "a1", "to": "a2", "why": "w", "signals": "test"}]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = run(xlsx, p, log, apply=True)
    assert r.returncode != 0


def test_letter_citation_in_explanation_fails(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-1", "field": "Wyjaśnienie", "from": "Bo tak (Image 5).", "to": "Odpowiedź A jest poprawna.", "why": "w", "signals": "test"}]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = run(xlsx, p, log, apply=True)
    assert r.returncode != 0


def test_rerun_is_idempotent(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-1", "field": "Wyjaśnienie", "from": "Bo tak (Image 5).", "to": "Bo tak.", "why": "w", "signals": "test"}]
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    assert run(xlsx, p, log, apply=True).returncode == 0
    r2 = run(xlsx, p, log, apply=True)  # powtórka: crash-recovery / omyłkowe drugie uruchomienie
    assert r2.returncode == 0, r2.stderr
    assert "już naniesione" in r2.stdout
    assert len(json.loads(log.read_text(encoding="utf-8"))) == 1  # dziennik bez duplikatu


def test_duplicate_options_fail(tmp_path):
    xlsx = tmp_path / "t.xlsx"
    make_xlsx(xlsx)
    log = tmp_path / "log.json"
    log.write_text("[]", encoding="utf-8")
    props = [{"sheet": "1.Testowy", "row": 2, "id": "T-1", "field": "B", "from": "b1", "to": "A1 ", "why": "w", "signals": "test"}]  # po normalizacji zrówna się z opcją A
    p = tmp_path / "p.json"
    p.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = run(xlsx, p, log, apply=True)
    assert r.returncode != 0
    ws = openpyxl.load_workbook(xlsx)["1.Testowy"]
    assert ws.cell(2, FIELD_COL["B"]).value == "b1"  # nic nie zapisano
```

- [ ] **Step 2: Uruchom testy — mają POLEC**

Run: `python3 -m pytest scripts/validation/test_apply_field_changes.py -v`
Expected: FAIL/ERROR — `apply_field_changes.py` nie istnieje.

- [ ] **Step 3: Napisz `scripts/validation/apply_field_changes.py`**

```python
#!/usr/bin/env python3
"""Nanosi propozycje zmian na xlsx i dopisuje je do dziennika. Jedyna droga zapisu do neuro_questions.xlsx w przebiegach detells."""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from generate_quiz_data import cell_text, cites_letter  # noqa: E402

FIELD_COL = {"ID": 1, "Pytanie": 2, "A": 3, "B": 4, "C": 5, "D": 6, "Poprawna": 7, "Wyjaśnienie": 8, "Wykluczone": 10}
IMG = re.compile(r"\bimage\b", re.IGNORECASE)


def fail(msg):
    sys.exit(f"BŁĄD: {msg}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("proposals")
    ap.add_argument("--log", default=str(HERE.parent.parent / "docs" / "validation" / "applied-changes.json"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    import openpyxl
    props = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
    if not isinstance(props, list) or not props:
        fail("plik propozycji pusty albo nie jest listą")
    wb = openpyxl.load_workbook(args.xlsx)
    applied, skipped = [], 0
    for i, p in enumerate(props):
        missing = [k for k in ("sheet", "row", "id", "field", "from", "to", "why", "signals") if k not in p]
        if missing:
            fail(f"propozycja {i}: brak pól {missing}")
        if p["field"] not in FIELD_COL:
            fail(f"propozycja {i}: nieznane pole '{p['field']}'")
        if str(p["from"]) == str(p["to"]):
            fail(f"propozycja {i} ({p['sheet']} w.{p['row']}): 'from' == 'to' (pusta zmiana zaśmieca dziennik)")
        ws = wb[p["sheet"]]
        cur_id = cell_text(ws.cell(p["row"], FIELD_COL["ID"]))
        if cur_id != p["id"]:
            fail(f"{p['sheet']} w.{p['row']}: ID w arkuszu '{cur_id}' != '{p['id']}' (przesunięcie wierszy?)")
        cur = cell_text(ws.cell(p["row"], FIELD_COL[p["field"]]))
        if cur == p["to"]:
            skipped += 1  # idempotentny re-run: zmiana już w pliku (crash między save a logiem albo powtórka)
            print(f"POMINIĘTO (już naniesione) {p['sheet']} w.{p['row']} [{p['field']}]")
            continue
        if cur != p["from"]:
            fail(f"{p['sheet']} w.{p['row']} [{p['field']}]: wartość bieżąca różna od 'from' (stale?)\n  jest: {cur[:120]}\n  from: {str(p['from'])[:120]}")
        if not str(p["to"]).strip():
            fail(f"{p['sheet']} w.{p['row']} [{p['field']}]: puste 'to'")
        if p["field"] == "Wyjaśnienie":
            if IMG.search(p["to"]):
                fail(f"{p['sheet']} w.{p['row']}: 'to' nadal zawiera odniesienie do Image")
            if cites_letter(p["to"]):
                fail(f"{p['sheet']} w.{p['row']}: 'to' cytuje literę odpowiedzi (opcje są tasowane)")
        if args.apply:
            ws.cell(p["row"], FIELD_COL[p["field"]]).value = p["to"]
        applied.append(p)
        print(f"OK {p['sheet']} w.{p['row']} [{p['field']}]: {str(p['from'])[:60]!r} -> {str(p['to'])[:60]!r}")
    by_row = {}  # opcje wiersza po edycji muszą być parami różne; w dry-run nakładamy propozycje na odczyt
    for p in applied:
        if p["field"] in ("A", "B", "C", "D"):
            by_row.setdefault((p["sheet"], p["row"]), {})[p["field"]] = p["to"]
    for (sheet, row), edits in sorted(by_row.items()):
        ws = wb[sheet]
        opts = [re.sub(r"\s+", " ", str(edits.get(f, cell_text(ws.cell(row, FIELD_COL[f])))).lower()).strip() for f in ("A", "B", "C", "D")]
        if len(set(opts)) != 4:
            fail(f"{sheet} w.{row}: opcje po edycji nie są parami różne: {opts}")
    if args.apply:
        wb.save(args.xlsx)
        log_path = Path(args.log)
        log = json.loads(log_path.read_text(encoding="utf-8"))
        seen = {json.dumps(e, sort_keys=True, ensure_ascii=False) for e in log}
        new = [p for p in applied if json.dumps(p, sort_keys=True, ensure_ascii=False) not in seen]
        log.extend(new)
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Zapisano {len(applied)} zmian do {args.xlsx} (nowe wpisy w dzienniku: {len(new)}, pominięte już naniesione: {skipped})")
    else:
        print(f"DRY-RUN: {len(applied)} propozycji poprawnych (pominięte już naniesione: {skipped}), nic nie zapisano")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Testy mają PRZEJŚĆ**

Run: `python3 -m pytest scripts/validation/test_apply_field_changes.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/validation/apply_field_changes.py scripts/validation/test_apply_field_changes.py
git commit -m "feat: add apply_field_changes.py — walidujący zapis zmian do xlsx z logiem"
```

---

### Task 3: Mechaniczne usunięcie nawiasowych „(Image N)" — 141 wyjaśnień

**Files:**
- Create: `scripts/validation/propose_image_strip.py`
- Modify: `data/neuro_questions.xlsx` (przez applier), `docs/validation/applied-changes.json`

**Interfaces:**
- Consumes: `docs/validation/detells/baseline.json` (Task 1), applier (Task 2).
- Produces: `docs/validation/detells/props-image-strip.json` — propozycje dla wyjaśnień, w których po zdjęciu nawiasów „Image" nie zostaje żadne odniesienie.

- [ ] **Step 1: Napisz `scripts/validation/propose_image_strip.py`**

```python
#!/usr/bin/env python3
"""Generuje propozycje mechanicznego usunięcia nawiasowych odniesień '(Image N)' z wyjaśnień."""
import json
import re
import sys
from pathlib import Path

IMG = re.compile(r"\bimage\b", re.IGNORECASE)
IMG_PAREN = re.compile(r"\s*\((?:zob\.\s*|por\.\s*)?Image[^)]*\)", re.IGNORECASE)


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
```

- [ ] **Step 2: Wygeneruj propozycje i obejrzyj próbkę**

Run: `python3 scripts/validation/propose_image_strip.py docs/validation/detells/baseline.json docs/validation/detells/props-image-strip.json`
Expected: `propozycji: 141`. Przejrzyj ręcznie 10 pierwszych `to` — zdania mają być gramatycznie kompletne (nawias był wtrąceniem).

- [ ] **Step 3: Dry-run appliera, potem apply**

Run: `python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-image-strip.json`
Expected: `DRY-RUN: 141 propozycji poprawnych`.
Run: `python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-image-strip.json --apply`
Expected: `Zapisano 141 zmian`.

- [ ] **Step 4: Pomiar kontrolny**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/after-task3.json`
Expected: `image: 180 (nawiasowe 0, wplecione 180)`; pozostałe metryki bez zmian względem baseline.

- [ ] **Step 5: Commit**

```bash
git add data/neuro_questions.xlsx scripts/validation/propose_image_strip.py
git commit -m "fix: strip parenthetical figure references from 141 explanations"
```

---

### Task 4: Przeredagowanie 180 wyjaśnień z wplecionym „Image" (LLM)

**Files:**
- Create: `scripts/validation/prepare_batches.py` (generyczny podział na paczki — używany też w Taskach 5–7)
- Create (robocze): `docs/validation/detells/batches-image/batch-NN.json`, `docs/validation/detells/results-image/batch-NN.json`
- Modify: `data/neuro_questions.xlsx`, `docs/validation/applied-changes.json`

**Interfaces:**
- Consumes: `after-task3.json` (Task 3), applier (Task 2).
- Produces: `prepare_batches.py <report.json> <klucz> <out-dir> <batch-size>` — dzieli listę pytań z raportu (`klucz` = `image` | `paren_only` | `catg_wrong` | `balance`) na pliki `batch-NN.json`, każdy: lista pełnych rekordów pytań. Wyniki agentów: pliki o tej samej nazwie w katalogu wyników, w formacie propozycji appliera.

- [ ] **Step 1: Napisz `scripts/validation/prepare_batches.py`**

```python
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
```

- [ ] **Step 2: Wygeneruj paczki**

Run: `python3 scripts/validation/prepare_batches.py docs/validation/detells/after-task3.json image docs/validation/detells/batches-image 30`
Expected: `180 pytań -> 6 paczek`.

- [ ] **Step 3: Wyślij 6 agentów (Sonnet, równolegle), jeden na paczkę**

Prompt (wstaw NN i ścieżki absolutne; agent dostaje ŚCIEŻKI, nie treść):

```
Przeczytaj plik docs/validation/detells/batches-image/batch-NN.json — listę pytań quizowych z neuroanatomii.
Pole "explanation" każdego rekordu odwołuje się do ryciny ("Image N"), której użytkownik quizu nie widzi.
Przeredaguj każde wyjaśnienie tak, aby stwierdzało fakt wprost, bez jakiegokolwiek odwołania do ryciny/Image.
Zasady twarde:
- NIE zmieniaj treści merytorycznej — żadnych nowych faktów, żadnych usuniętych faktów poza samym odwołaniem do ryciny.
- NIE odwołuj się do liter odpowiedzi (A/B/C/D) — opcje są tasowane.
- Zachowaj resztę zdania i styl; zmiana ma być minimalna (np. "Według Image 19, dolna ściana grubieje" -> "Dolna ściana grubieje").
- Wynik zapisuj NA BIEŻĄCO do docs/validation/detells/results-image/batch-NN.json jako listę obiektów:
  {"sheet", "row", "id", "field": "Wyjaśnienie", "from": <dokładna wartość pola explanation z wejścia>, "to": <nowe wyjaśnienie>,
   "why": "wyjaśnienie odsyłało do ryciny materiału źródłowego, niewidocznej w quizie", "signals": "przeredagowanie odniesienia do ryciny"}
- Po zakończeniu wypisz tylko liczbę przetworzonych rekordów.
```

- [ ] **Step 4: Scal wyniki i zastosuj**

```bash
python3 - <<'EOF'
import json
from pathlib import Path
props = []
for f in sorted(Path("docs/validation/detells/results-image").glob("batch-*.json")):
    props.extend(json.loads(f.read_text(encoding="utf-8")))
assert len(props) == 180, f"jest {len(props)}, oczekiwano 180"
Path("docs/validation/detells/props-image-rewrite.json").write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(props))
EOF
python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-image-rewrite.json
python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-image-rewrite.json --apply
```

Expected: dry-run bez błędów (applier sam odrzuci pozostawione „Image" i cytowanie liter), potem `Zapisano 180 zmian`. Jeśli applier zgłosi błędy w pojedynczych rekordach — poprawić TE rekordy (ponowny mini-przebieg agenta), nie obchodzić walidacji.

- [ ] **Step 5: Pomiar kontrolny + QC próbki**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/after-task4.json`
Expected: `image: 0 (nawiasowe 0, wplecione 0)`.
QC: przeczytaj 15 losowych par from/to z `props-image-rewrite.json` — sens merytoryczny nie zmieniony. Wątpliwości → porównanie z dossier tematu.

- [ ] **Step 6: Commit**

```bash
git add data/neuro_questions.xlsx scripts/validation/prepare_batches.py
git commit -m "fix: rewrite 180 explanations to drop embedded figure references"
```

---

### Task 5: Nawias tylko-w-poprawnej — 359 pytań

**Files:**
- Create: `scripts/validation/blind_pack.py`
- Create (robocze): `docs/validation/detells/batches-paren/`, `docs/validation/detells/results-paren/`, `docs/validation/detells/verify-paren/`
- Modify: `data/neuro_questions.xlsx`, `docs/validation/applied-changes.json`

**Interfaces:**
- Consumes: `after-task4.json`, `prepare_batches.py`, applier, `measure_tells.load_questions`.
- Produces: propozycje zmian pól `A`–`D` (opcja poprawna bez nawiasu) i `Wyjaśnienie` (wchłania treść nawiasu, jeśli jej tam nie ma). Dodatkowo `blind_pack.py <records.json> <out-blind.json> <out-key.json> [sample-N]` — z rekordów w formacie `measure_tells` buduje wejście dla ślepego solvera: BEZ pola `correct`, z opcjami przetasowanymi deterministycznie (seed `sheet:row`); permutacje i klucz idą do osobnego pliku. Używany też w Tasku 7.

- [ ] **Step 1: Paczki**

Run: `python3 scripts/validation/prepare_batches.py docs/validation/detells/after-task4.json paren_only docs/validation/detells/batches-paren 30`
Expected: `359 pytań -> 12 paczek`.

- [ ] **Step 2: Wyślij 12 agentów (Sonnet, równolegle)**

Prompt:

```
Przeczytaj plik docs/validation/detells/batches-paren/batch-NN.json — pytania quizowe, w których TYLKO poprawna opcja
(indeks "correct" w liście "options", 0=A..3=D) zawiera nawias z dopowiedzeniem. To zdradza odpowiedź osobie zgadującej.
Dla każdego pytania wybierz jedno:
- MOVE: usuń nawias z poprawnej opcji; jeśli wyjaśnienie nie zawiera tej informacji, dopisz ją tam jednym zdaniem.
- KEEP: zostaw bez zmian — wyłącznie gdy nawias jest niezbędny, by opcja była jednoznaczna albo gdy to nawias jest testowaną treścią.
- DROP: usuń nawias bez przenoszenia — wyłącznie gdy wyjaśnienie już zawiera tę informację.
Zasady twarde:
- NIE zmieniaj sensu opcji; po usunięciu nawiasu opcja musi zostać poprawną odpowiedzią na pytanie.
- NIE odwołuj się w wyjaśnieniu do liter odpowiedzi (A/B/C/D).
- KEEP ma być rzadkie (cel: ≤10% paczki) i zawsze z uzasadnieniem.
- Wynik zapisuj NA BIEŻĄCO do docs/validation/detells/results-paren/batch-NN.json:
  lista propozycji {"sheet","row","id","field","from","to","why","signals":"balans opcji: nawias tylko w poprawnej"} —
  dla MOVE zwykle dwie propozycje (pole opcji, np. "B", oraz "Wyjaśnienie"); dla KEEP zero propozycji, ale dopisz rekord
  do osobnej listy w tym samym pliku pod kluczem "kept": {"sheet","row","id","uzasadnienie"}.
  Format pliku: {"props": [...], "kept": [...]}. Pole "from" = DOKŁADNA bieżąca wartość z wejścia.
- Po zakończeniu wypisz liczby: propozycji i KEEP.
```

- [ ] **Step 3: Scal, dry-run, apply**

```bash
python3 - <<'EOF'
import json
from pathlib import Path
props, kept = [], []
for f in sorted(Path("docs/validation/detells/results-paren").glob("batch-*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    props.extend(d["props"])
    kept.extend(d["kept"])
Path("docs/validation/detells/props-paren.json").write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
Path("docs/validation/detells/kept-paren.json").write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"props: {len(props)}, kept: {len(kept)}")
EOF
python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-paren.json
python3 scripts/validation/apply_field_changes.py data/neuro_questions.xlsx docs/validation/detells/props-paren.json --apply
```

Expected: kept ≤ 36; dry-run czysty; apply zapisany.

- [ ] **Step 4: Napisz `scripts/validation/blind_pack.py` i zweryfikuj próbkę ślepym solverem**

```python
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
```

Zbuduj próbkę 40 z wierszy dotkniętych edycją opcji (stan xlsx PO apply):

```bash
python3 - <<'EOF'
import json
import sys
from pathlib import Path
sys.path.insert(0, "scripts/validation")
from measure_tells import load_questions
touched = {(p["sheet"], p["row"]) for p in json.loads(Path("docs/validation/detells/props-paren.json").read_text(encoding="utf-8")) if p["field"] in "ABCD"}
recs = [q for q in load_questions("data/neuro_questions.xlsx") if (q["sheet"], q["row"]) in touched]
Path("docs/validation/detells/verify-paren/records.json").write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
print(len(recs))
EOF
python3 scripts/validation/blind_pack.py docs/validation/detells/verify-paren/records.json docs/validation/detells/verify-paren/blind.json docs/validation/detells/verify-paren/key.json 40
```

Agent-solver (Sonnet), prompt:

```
Przeczytaj docs/validation/detells/verify-paren/blind.json — pytania z neuroanatomii z czterema opcjami (bez klucza).
Odpowiedz na każde na podstawie wiedzy z zakresu podręcznikowej neuroanatomii. Wynik zapisuj NA BIEŻĄCO do
docs/validation/detells/verify-paren/answers.json jako listę {"sheet","row","answer_index"} (indeks 0-3 w podanej kolejności opcji).
Nie zgaduj wzorców tekstowych — odpowiadasz merytorycznie. Po zakończeniu wypisz liczbę odpowiedzi.
```

Porównanie:

```bash
python3 - <<'EOF'
import json
from pathlib import Path
key = {(k["sheet"], k["row"]): k["correct_blind_index"] for k in json.loads(Path("docs/validation/detells/verify-paren/key.json").read_text(encoding="utf-8"))}
ans = json.loads(Path("docs/validation/detells/verify-paren/answers.json").read_text(encoding="utf-8"))
hits = sum(1 for a in ans if key[(a["sheet"], a["row"])] == a["answer_index"])
print(f"{hits}/{len(ans)}")
assert len(ans) == len(key)
EOF
```

Expected: ≥ 38/40 (95%). Poniżej progu: obejrzeć chybione pytania — jeśli edycja odebrała opcji jednoznaczność, cofnąć te zmiany (`git diff` na xlsx + odwrotne propozycje) i przejrzeć całą partię pod tym kątem.

- [ ] **Step 5: Pomiar kontrolny**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/after-task5.json`
Expected: `paren_only` ≤ 36; „poprawna najkrótsza" ≤ 12% (strażnik regresji). Uwaga: `len15`/`conj_only` mogą drgnąć (opcje się skróciły, wyjaśnienia wydłużyły) — to oczekiwane; Task 7 pracuje na świeżym pomiarze.

- [ ] **Step 6: Commit**

```bash
git add data/neuro_questions.xlsx scripts/validation/blind_pack.py
git commit -m "fix: move parenthetical clarifications from correct options to explanations"
```

---

### Task 6: Zwroty kategoryczne w dystraktorach — 99 pytań

**Files:**
- Create (robocze): `docs/validation/detells/batches-catg/`, `docs/validation/detells/results-catg/`, `docs/validation/detells/verify-catg/`
- Modify: `data/neuro_questions.xlsx`, `docs/validation/applied-changes.json`

**Interfaces:**
- Consumes: `after-task5.json`, `prepare_batches.py`, applier, dossier z `scripts/validation/build_question_dossiers.py` (tf-idf po treści pytania i opcji na stronach z `docs/source-text/`).
- Produces: propozycje zmian pól `A`–`D` (złagodzone dystraktory) po weryfikacji błędności.

**Ryzyko kluczowe:** zdjęcie „tylko/zawsze/nigdy" może uczynić dystraktor PRAWDZIWYM („występuje tylko w X" jest fałszywe, „występuje w X" bywa prawdziwe). Dlatego każda zmiana przechodzi weryfikację względem dossier, a gdy złagodzenie robi zdanie prawdziwym — agent ma przebudować dystraktor na inne, jednoznacznie fałszywe stwierdzenie o zbliżonej długości.

- [ ] **Step 1: Paczki + dossier**

Run: `python3 scripts/validation/prepare_batches.py docs/validation/detells/after-task5.json catg_wrong docs/validation/detells/batches-catg 25`
Expected: 4 paczki. Następnie zbuduj dossier per paczka skryptem pomocniczym (wzorzec importu jak w `build_question_dossiers.py`: `page_index` + wybór stron per pytanie, zapis do `docs/validation/detells/batches-catg/dossier-NN.md` z nagłówkami stron).

- [ ] **Step 2: Wyślij 4 agentów-edytorów (Sonnet)**

Prompt:

```
Przeczytaj docs/validation/detells/batches-catg/batch-NN.json (pytania; "correct" to indeks poprawnej opcji)
oraz docs/validation/detells/batches-catg/dossier-NN.md (wycinki podręcznika — jedyne źródło prawdy).
W tych pytaniach ≥2 błędne opcje zawierają zwroty kategoryczne (tylko/wyłącznie/nigdy/zawsze/jedynie/każdy/wszystkie/żaden),
a poprawna ich nie ma — kategoryczność wskazuje błędną opcję.
Dla każdej błędnej opcji ze zwrotem kategorycznym: usuń lub zastąp zwrot tak, aby opcja POZOSTAŁA jednoznacznie fałszywa
według dossier. Jeśli po złagodzeniu zdanie staje się prawdziwe — przebuduj dystraktor na inne fałszywe stwierdzenie
o zbliżonej długości i tym samym stylu. NIE dotykaj poprawnej opcji ani wyjaśnienia, chyba że wyjaśnienie odnosi się
do zmienionej treści dystraktora — wtedy dołóż propozycję dla pola "Wyjaśnienie".
Wynik NA BIEŻĄCO do docs/validation/detells/results-catg/batch-NN.json — lista propozycji
{"sheet","row","id","field","from","to","why","signals":"złagodzenie kategorycznego dystraktora"};
w "why" umieść cytat z dossier potwierdzający, że nowa treść jest fałszywa (z numerem strony książki).
Po zakończeniu wypisz liczbę propozycji.
```

- [ ] **Step 3: Weryfikacja błędności (2 agenty Sonnet, po 2 paczki wyników)**

Prompt weryfikatora:

```
Przeczytaj docs/validation/detells/results-catg/batch-NN.json i dossier docs/validation/detells/batches-catg/dossier-NN.md.
Dla każdej propozycji zmiany opcji oceń WYŁĄCZNIE: czy nowa treść ("to") jest fałszywą odpowiedzią na pytanie
(pytanie znajdziesz w docs/validation/detells/batches-catg/batch-NN.json po sheet+row)? Werdykt per propozycja:
FALSZYWA_OK / PRAWDZIWA_BLAD / NIEROZSTRZYGALNE_Z_DOSSIER + jedno zdanie uzasadnienia.
Zapisuj NA BIEŻĄCO do docs/validation/detells/verify-catg/batch-NN.json. Nie proponuj poprawek — tylko werdykty.
```

Propozycje z werdyktem `PRAWDZIWA_BLAD` odrzucić (dystraktor wraca do edytora w mini-przebiegu); `NIEROZSTRZYGALNE_Z_DOSSIER` → do rozjemstwa w Tasku 7 Step 5 (ta sama mechanika) albo KEEP, jeśli pojedyncze.

- [ ] **Step 4: Scal zweryfikowane, dry-run, apply, pomiar**

Scal analogicznie do Tasku 5 (tylko propozycje FALSZYWA_OK) do `props-catg.json`, dry-run, apply.
Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/after-task6.json`
Expected: `catg_wrong` ≤ 10.

- [ ] **Step 5: Commit**

```bash
git add data/neuro_questions.xlsx
git commit -m "fix: soften categorical wording in distractors without breaking their falsity"
```

---

### Task 7: Balans długości, koniunkcji i wyliczeń — największy przebieg (~900–1000 pytań)

**Files:**
- Create: `scripts/validation/prepare_balance.py`
- Create (robocze): `docs/validation/detells/batches-balance/` (paczki + dossier), `results-balance/`, `verify-input/` i `verify-key/` (zaślepione wejścia solvera + permutacje z kluczem), `verify-balance/` (werdykty solver-/kontroler-), `adjudicate-balance/`
- Modify: `data/neuro_questions.xlsx`, `docs/validation/applied-changes.json`

**Interfaces:**
- Consumes: świeży pomiar po Tasku 6 (`after-task6.json`), `build_question_dossiers.py` (funkcje wyboru stron), `blind_pack.py` (Task 5), applier.
- Produces: `prepare_balance.py <report.json> <out-dir> <batch-size>` — wybiera unię `len15 ∪ conj_only ∪ comma_only` z raportu, deduplikuje po (sheet,row), grupuje PO ARKUSZACH (spójne dossier), emituje `batch-NN.json` + `dossier-NN.md`.

**Strategia edycji (w tej kolejności preferencji):**
1. **Skróć poprawną opcję** — usuń dopowiedzenia, przenieś szczegół do wyjaśnienia. Najbezpieczniejsze: nie dotyka dystraktorów.
2. **Rozbuduj 1–2 dystraktory** do struktury równoległej z poprawną (koniunkcja w poprawnej → koniunkcja także w dystraktorze), treścią z dossier, która pozostaje fałszywa jako całość.
3. Oba naraz, gdy dysproporcja duża.

- [ ] **Step 1: Świeży pomiar bazowy i `prepare_balance.py`**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/before-task7.json`

```python
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
```

(API zweryfikowane w kodzie: `build_dossiers.load_pages()` zwraca strony z polami `book`/`pdf`/`text`; `build_question_dossiers.page_index(pages)` zwraca `(tf_list, idf)`; `group_items(items, pages, tf_list, idf, per_group, k)` przypisuje pytaniom strony przez tf-idf i skleja grupy o zbliżonym zestawie stron; `render(pages, idx_list)` składa dossier z nagłówkami `## [str. książki m | PDF n]`. Pole `options` w `group_items` musi być dict-em — stąd adaptacja.)

Uwaga na liczność paczek: `group_items` tnie grupę, gdy unia stron przekroczy `k*3` — paczki będą różnej wielkości, zwykle mniejsze niż `per_group`. To zamierzone (mniejsze dossier na agenta).

Run: `python3 scripts/validation/prepare_balance.py docs/validation/detells/before-task7.json docs/validation/detells/batches-balance 25`
Expected: ~900–1000 pytań podzielonych na kilkadziesiąt paczek; liczba w stdout.

- [ ] **Step 2: Edytorzy (Sonnet), falami po 6–8 agentów, jeden na paczkę**

Prompt:

```
Przeczytaj docs/validation/detells/batches-balance/batch-NN.json i dossier-NN.md (wycinki podręcznika — jedyne źródło prawdy).
Każde pytanie ma pole "tells" — które wyróżniki zdradzają poprawną opcję (indeks "correct", 0=A..3=D):
len15 = poprawna ≥1,5x dłuższa od pozostałych; conj_only = tylko poprawna ma "i/oraz"; comma_only = tylko poprawna ma wyliczenie.
Zadanie: usuń wyróżnik minimalną edycją, w kolejności preferencji:
1) SKRÓĆ poprawną opcję (usuń dopowiedzenia; szczegół przenieś do wyjaśnienia, jeśli go tam nie ma);
2) ROZBUDUJ 1-2 dystraktory do struktury równoległej z poprawną — treścią z dossier, która JAKO CAŁOŚĆ pozostaje fałszywa;
3) oba naraz przy dużej dysproporcji.
Zasady twarde:
- Poprawna opcja po edycji MUSI pozostać poprawną i jednoznaczną odpowiedzią; dystraktory MUSZĄ pozostać fałszywe.
- Wszystkie opcje mają zgadzać się gramatycznie z pytaniem (przypadek, liczba, rodzaj).
- Po edycji długości opcji mają być zbliżone: najdłuższa < 1,4x drugiej najdłuższej; jeśli poprawna ma "i/oraz" lub wyliczenie,
  co najmniej jeden dystraktor też ma je mieć (lub poprawna ma ich nie mieć).
- NIE zmieniaj klucza (pole "correct" zostaje). NIE dodawaj zwrotów kategorycznych do dystraktorów.
- Jeśli edytujesz opcję, sprawdź wyjaśnienie: nie może bronić usuniętej treści ani przeczyć nowej — w razie potrzeby dołóż
  propozycję dla pola "Wyjaśnienie" (bez odwołań do liter A-D).
- Gdy pytania nie da się zbalansować bez naruszenia sensu (np. poprawna odpowiedź z natury złożona), oznacz SKIP z uzasadnieniem.
Wynik NA BIEŻĄCO do docs/validation/detells/results-balance/batch-NN.json:
{"props": [{"sheet","row","id","field","from","to","why","signals":"balans opcji (długość/koniunkcja/wyliczenie)"}],
 "skipped": [{"sheet","row","id","uzasadnienie"}]}
W "why" każdej zmiany dystraktora — cytat z dossier (ze stroną książki) potwierdzający fałszywość.
Po zakończeniu wypisz liczby: props, skipped.
```

Po każdej fali: sprawdź, że pliki wyników istnieją i parsują się; dopiero potem następna fala.

- [ ] **Step 3: Weryfikacja dwoma niezależnymi sygnałami — fizycznie zaślepiony solver + kontroler z kluczem**

Solver NIE może dostać pliku zawierającego klucz — instrukcja „nie patrz na pole correct" nie usuwa kotwiczenia. Najpierw zbuduj zaślepione wejścia (nałożenie propozycji na paczkę + `blind_pack.py` z Tasku 5):

```bash
python3 - <<'EOF'
import json
import subprocess
import sys
from pathlib import Path
LETTER = {"A": 0, "B": 1, "C": 2, "D": 3}
bdir = Path("docs/validation/detells/batches-balance")
rdir = Path("docs/validation/detells/results-balance")
vin = Path("docs/validation/detells/verify-input")
vkey = Path("docs/validation/detells/verify-key")
vin.mkdir(parents=True, exist_ok=True)
vkey.mkdir(parents=True, exist_ok=True)
for rf in sorted(rdir.glob("batch-*.json")):
    batch = {(q["sheet"], q["row"]): q for q in json.loads((bdir / rf.name).read_text(encoding="utf-8"))}
    props = json.loads(rf.read_text(encoding="utf-8"))["props"]
    for p in props:  # nakładamy edycje: pytania w wejściu solvera są w stanie PO proponowanej zmianie
        q = batch[(p["sheet"], p["row"])]
        if p["field"] in LETTER:
            q["options"][LETTER[p["field"]]] = p["to"]
    touched = {(p["sheet"], p["row"]) for p in props}
    recs = [q for k, q in batch.items() if k in touched]
    tmp = vin / f"records-{rf.stem}.json"
    tmp.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    subprocess.run([sys.executable, "scripts/validation/blind_pack.py", str(tmp), str(vin / rf.name), str(vkey / rf.name)], check=True)
EOF
```

Agent-SOLVER (Sonnet), jeden na 2 paczki, prompt:

```
Przeczytaj docs/validation/detells/verify-input/batch-NN.json — pytania z neuroanatomii z czterema opcjami (bez klucza) —
oraz docs/validation/detells/batches-balance/dossier-NN.md (wycinki podręcznika). Odpowiedz na każde pytanie na podstawie
dossier i wiedzy podręcznikowej. Wynik zapisuj NA BIEŻĄCO do docs/validation/detells/verify-balance/solver-batch-NN.json
jako listę {"sheet","row","answer_index"} (indeks 0-3 w podanej kolejności opcji). Nie zgaduj wzorców tekstowych.
Po zakończeniu wypisz liczbę odpowiedzi.
```

Agent-KONTROLER (Sonnet), jeden na 2 paczki, prompt (kontroler widzi klucz — to drugi, jawny sygnał):

```
Przeczytaj docs/validation/detells/batches-balance/batch-NN.json (pytania, "correct" to indeks poprawnej opcji),
docs/validation/detells/results-balance/batch-NN.json (propozycje edycji) i dossier-NN.md (jedyne źródło prawdy).
Dla każdej propozycji oceń: edytowany dystraktor pozostaje fałszywy według dossier? skrócona poprawna pozostaje poprawna
i jednoznaczna? zmienione wyjaśnienie nie przeczy opcjom i nie broni usuniętej treści? Zapisuj NA BIEŻĄCO do
docs/validation/detells/verify-balance/kontroler-batch-NN.json listę
{"sheet","row","field","werdykt":"CZYSTO"|"ZASTRZEŻENIE","uzasadnienie":<jedno zdanie z odwołaniem do dossier>}.
Nie proponuj poprawek — tylko werdykty.
```

- [ ] **Step 4: Scal werdykty (odtasowanie po kluczu), dry-run, apply (per fala arkuszy)**

ZGODA dla pytania = solver trafił (`answer_index == correct_blind_index` z `verify-key/batch-NN.json`) ORAZ wszystkie jego propozycje mają werdykt CZYSTO. Scal propozycje pytań ZGODA do `props-balance-NN.json`:

```bash
python3 - <<'EOF'
import json
from pathlib import Path
rdir = Path("docs/validation/detells/results-balance")
vdir = Path("docs/validation/detells/verify-balance")
kdir = Path("docs/validation/detells/verify-key")
ok_props, disputes = [], []
for rf in sorted(rdir.glob("batch-*.json")):
    props = json.loads(rf.read_text(encoding="utf-8"))["props"]
    key = {(k["sheet"], k["row"]): k["correct_blind_index"] for k in json.loads((kdir / rf.name).read_text(encoding="utf-8"))}
    solver = {(a["sheet"], a["row"]): a["answer_index"] for a in json.loads((vdir / f"solver-{rf.stem}.json").read_text(encoding="utf-8"))}
    kontroler = json.loads((vdir / f"kontroler-{rf.stem}.json").read_text(encoding="utf-8"))
    bad_rows = {(v["sheet"], v["row"]) for v in kontroler if v.get("werdykt") != "CZYSTO"}
    for p in props:
        rr = (p["sheet"], p["row"])
        if solver.get(rr) == key.get(rr) and rr not in bad_rows:
            ok_props.append(p)
        else:
            disputes.append(p)
print(f"ZGODA: {len(ok_props)} propozycji, SPOR: {len(disputes)}")
Path("docs/validation/detells/props-balance-ok.json").write_text(json.dumps(ok_props, ensure_ascii=False, indent=1), encoding="utf-8")
Path("docs/validation/detells/disputes-balance.json").write_text(json.dumps(disputes, ensure_ascii=False, indent=1), encoding="utf-8")
EOF
```

Dry-run appliera na `props-balance-ok.json`, apply, commit częściowy:

```bash
git add data/neuro_questions.xlsx
git commit -m "fix: balance option length and structure (batch NN..MM)"
```

- [ ] **Step 5: Rozjemstwo sporów**

Propozycje z `disputes-balance.json` (Step 4) pogrupuj do `docs/validation/detells/adjudicate-balance/`. Grupuj PO STRONACH KSIĄŻKI (jak w poprzedniej walidacji): jeden agent-rozjemca (model najmocniejszy) dostaje zakres stron skanu RAZ i listę wszystkich sporów z tych stron. Przelicznik: strona PDF = strona książki − 3. Rozjemca wydaje decyzję per spór: przyjąć propozycję / odrzucić / własna korekta (w formacie propozycji). Decyzje → osobny plik propozycji → dry-run → apply → log z `signals: "rozjemca (oryginalny skan)"`.

- [ ] **Step 6: Pomiar kontrolny**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/after-task7.json`
Expected: `len15` ≤ 170, `conj_only` ≤ 40, `comma_only` ≤ 10, poprawna najdłuższa ≤ 35%. Niespełnione → dodatkowy przebieg na pozostałych pytaniach (te same skrypty, świeży pomiar) — decyzja z użytkownikiem, jeśli koszt ma przekroczyć ~2 mln tokenów ponad plan.

---

### Task 8: Akceptacja końcowa, regeneracja danych, dokumentacja

**Files:**
- Modify: `public/data/` (regeneracja), `docs/validation/STATUS.md`
- Test: `npm test`, `python3 -m pytest scripts/`

- [ ] **Step 1: Pełny pomiar akceptacyjny**

Run: `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/final.json`
Expected: wszystkie cele z tabeli „Cele akceptacyjne" spełnione (w tym strażnik „najkrótszej": ≤ 12%, silnie ≤ 3%). Dodatkowo sekcja `token_ratios` finalnego raportu: token „lub" poza listą (ratio < 2), a pozostałe pozycje po przejrzeniu mają charakter merytoryczny (terminy anatomiczne skupione tematycznie), nie stylistyczny.

- [ ] **Step 2: Regeneracja JSON-ów i testy**

```bash
npm run data:generate
python3 -m pytest scripts/ -v
npm test
```

Expected: generacja bez błędów (liczba pytań w quizie niezmieniona — ten plan niczego nie wyklucza), wszystkie testy zielone. UWAGA: `npm run data:generate` modyfikuje `public/data/` — commitujemy razem ze źródłem.

- [ ] **Step 3: Sanity-check aplikacji**

Run: `npm run dev` (port 8080), przejść przez stronę startową (przyciski-pigułki działów → liczba pytań → „Rozpocznij test"), obejrzeć ~10 pytań z działów 9–10: wyjaśnienia bez „Image", opcje wyglądają naturalnie. (Wejście prosto na `/quiz?...` nie ładuje puli; na ekranie quizu pierwsze trzy przyciski to rozmiar czcionki.)

- [ ] **Step 4: Aktualizacja STATUS.md**

Dopisz sekcję ze stanem po tym przebiegu: data, liczby zmian per task (z `applied-changes.json` — policz wpisy per `signals`), tabela celów akceptacyjnych z wynikami, wnioski. Bez cytatów z podręcznika (plik jest publiczny).

- [ ] **Step 5: Commit + decyzja o publikacji**

```bash
git add data/neuro_questions.xlsx public/data/ docs/validation/STATUS.md
git commit -m "fix: eliminate answer-revealing patterns across the question pool"
```

STOP: push gałęzi `detells` do forka i PR do `agatajustyna/neuro-wiry-hub` — dopiero po potwierdzeniu przez użytkownika (`gh` niezainstalowany; PR przez www albo po instalacji `gh`).

---

## Szacunek kosztu

- Task 4: 180 przeredagowań, bez dossier — ~0,4 mln tokenów.
- Task 5: 359 pytań, bez dossier — ~0,8 mln.
- Task 6: 99 pytań + dossier + weryfikacja — ~0,5 mln.
- Task 7: ~900–1000 pytań × (edytor + ślepy solver + kontroler) z dossier ~2,4 tys. tokenów/pytanie/przebieg + rozjemstwo — ~6–7 mln.
- Razem: **~7–9 mln tokenów** (poprzednia pełna walidacja o podobnej mechanice: potwierdzone koszty per pytanie z STATUS.md).
