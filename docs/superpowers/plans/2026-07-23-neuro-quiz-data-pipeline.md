# Neuro Quiz — Potok danych (Plan 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rozszerzyć istniejący `xlsx_to_csv.py` w narzędzie admina, które z `neuro_questions.xlsx` generuje manifest (`public/data/index.json`) i pliki pytań per dział (`public/data/sections/<id>.json`), oraz dodać po stronie aplikacji schemat `zod` walidujący te pliki.

**Architecture:** Generator to offline'owe narzędzie admina w Pythonie (nie część builda strony), uruchamiane lokalnie: `python3 scripts/generate_quiz_data.py <xlsx>`. Reużywa sprawdzonej logiki `xlsx_to_csv.py` (czytanie xlsx, odwracanie autokonwersji Excela, parsowanie tagów, walidacja), zmienia tylko wyjście z CSV na JSON. Ponieważ generator jest w Pythonie, a aplikacja w TS, zgodności formatu pilnuje schemat `zod` po stronie strony — druga bramka łapiąca rozjazd.

**Tech Stack:** Python 3 + openpyxl (generator, już używane w sesji), TypeScript + zod (schemat, `zod` już w zależnościach), vitest (test zgodności). Menedżer pakietów: bun.

**Prerekwizyt:** Plan działa na obecnych danych. Jednorazowe przepisanie wyjaśnień (spec sekcja 6) jest niezależne — walidacja liter tu tylko OSTRZEGA, nie blokuje.

**Uwaga o źródle:** działający `xlsx_to_csv.py` leży w katalogu nadrzędnym (`../xlsx_to_csv.py` względem repo). Nowy generator to osobny plik w repo, portujący jego sprawdzone funkcje `cell_text` i `parse_tags`.

**Kanoniczne źródło prawdy:** dotąd xlsx edytowano w katalogu nadrzędnym (`../neuro_questions.xlsx`). Po Task 0 kanoniczną kopią jest `data/neuro_questions.xlsx` w repo — od tego momentu autor edytuje TĘ kopię i to na niej działa jednorazowe przepisanie wyjaśnień (spec sekcja 6). Kopia nadrzędna jest legacy; edytowanie jej po Task 0 grozi cichym dryfem danych.

---

## Struktura plików

- `scripts/generate_quiz_data.py` — generator (Python). Funkcje czyste: `slugify`, `parse_tags`, `cell_text`, `cites_letter`, `build_section_meta`; oraz `main()` z I/O.
- `scripts/test_generate_quiz_data.py` — testy czystych funkcji (plain assert, uruchamiane `python3`).
- `data/neuro_questions.xlsx` — kopia źródła prawdy w repo (backup w gicie).
- `public/data/index.json`, `public/data/sections/*.json` — wygenerowane, commitowane.
- `src/lib/quiz-data.ts` — schematy `zod` + typy przez `z.infer` (kontrakt strony).
- `src/lib/quiz-data.test.ts` — test vitest: wczytuje wygenerowane JSON-y i waliduje schematem (łapie rozjazd Python↔TS).
- `vitest.config.ts` — konfiguracja testów.
- `requirements.txt` — zależności Pythona generatora (`openpyxl`); nie jest w środowisku domyślnie.
- `package.json` — nowe skrypty `test`, `data:generate`; devDep `vitest` (zod już jest).

---

## Task 0: Setup (vitest, openpyxl, skrypty, kanoniczny xlsx)

**Files:**
- Modify: `package.json`
- Create: `vitest.config.ts`
- Create: `requirements.txt`
- Create: `data/neuro_questions.xlsx` (kopia — od teraz KANONICZNE źródło prawdy)

- [ ] **Step 1: Zainstaluj vitest**

Run:
```bash
cd /Users/adamdrzewiecki/IntelliJProjects/private/neuro_quiz/neuro-wiry-hub
bun add -d vitest vite-tsconfig-paths
```
Expected: `vitest` w `devDependencies`. `vite-tsconfig-paths` jest już w zależnościach — bun potwierdzi. `zod` NIE wymaga instalacji (już w `dependencies`). Jeśli `bunfig.toml` (`minimumReleaseAge`) zablokuje najnowszą wersję, wybierz starszą niż 24 h.

- [ ] **Step 2: Dodaj skrypty do package.json**

W bloku `"scripts"` dodaj:
```json
    "test": "vitest run",
    "data:generate": "python3 scripts/generate_quiz_data.py"
```

- [ ] **Step 3: Utwórz vitest.config.ts**

```ts
import { defineConfig } from "vitest/config";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths()],
  test: {
    include: ["src/**/*.test.ts", "scripts/**/*.test.ts"],
    environment: "node",
  },
});
```

- [ ] **Step 4: Zadeklaruj i zainstaluj zależność Pythona**

`openpyxl` NIE jest w środowisku domyślnie (brak `requirements.txt` w repo) — bez tego
generator i jego testy padają na `ModuleNotFoundError`. Utwórz `requirements.txt`:
```
openpyxl>=3.1
```
Run:
```bash
python3 -m pip install -r requirements.txt
python3 -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
```
Expected: openpyxl zainstalowany, wersja wypisana.

- [ ] **Step 5: Skopiuj źródłowy xlsx do repo i ustal go jako kanoniczny**

Źródło prawdy edytowano dotąd w katalogu nadrzędnym (`../neuro_questions.xlsx`).
**Po tym kroku kanoniczną kopią jest `data/neuro_questions.xlsx` w repo** — od teraz
autor edytuje TĘ kopię, a jednorazowe przepisanie wyjaśnień (spec sekcja 6) celuje
w nią. Kopia w katalogu nadrzędnym staje się legacy.

Run:
```bash
mkdir -p data
cp ../neuro_questions.xlsx data/neuro_questions.xlsx
ls -la data/neuro_questions.xlsx
```
Expected: plik ~4,3 MB w `data/`.

- [ ] **Step 6: Commit**

```bash
git add package.json bun.lock vitest.config.ts requirements.txt data/neuro_questions.xlsx
git commit -m "chore: setup vitest + openpyxl, add canonical source xlsx to repo"
```

---

## Task 1: Generator — czyste funkcje z testami

**Files:**
- Create: `scripts/generate_quiz_data.py`
- Test: `scripts/test_generate_quiz_data.py`

- [ ] **Step 1: Napisz test czystych funkcji**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_quiz_data import slugify, parse_tags, cites_letter


def test_slugify():
    assert slugify("Ogólne") == "ogolne"
    assert slugify("Kresomózgowie") == "kresomozgowie"
    assert slugify("Kora mózgu - płat czołowy") == "kora-mozgu-plat-czolowy"
    assert slugify("Czucie powierzchniowe") == "czucie-powierzchniowe"
    assert slugify("  Wyspa  ") == "wyspa"


def test_parse_tags():
    assert parse_tags("#nerw_VII #neuroanatomia #Krasucki") == ["nerw_vii", "neuroanatomia", "krasucki"]
    assert parse_tags("neuron, akson") == ["neuron", "akson"]
    assert parse_tags("#OUN #anatomia #oun") == ["oun", "anatomia"]
    assert parse_tags("") == []


def test_cites_letter():
    assert cites_letter("Odpowiedź C jest poprawna, bo...") is True
    assert cites_letter("B jest nieprawidłowa, ponieważ...") is True
    assert cites_letter("Nerwy czaszkowe to układ obwodowy.") is False
    assert cites_letter("Pole A należy do kory ruchowej.") is False


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"Wszystkie testy przeszły ({len(tests)})")
```

- [ ] **Step 2: Uruchom test — ma nie przejść**

Run: `python3 scripts/test_generate_quiz_data.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_quiz_data'` (plik jeszcze nie istnieje).

- [ ] **Step 3: Zaimplementuj generator z czystymi funkcjami**

```python
#!/usr/bin/env python3
"""Narzędzie admina: neuro_questions.xlsx -> public/data/index.json + sections/<id>.json.
Rozszerzenie xlsx_to_csv.py — ta sama logika czytania, wyjście JSON zamiast CSV."""
import datetime
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "public" / "data"

PL_MAP = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
})

LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


def slugify(text: str) -> str:
    lowered = text.lower().translate(PL_MAP)
    decomposed = unicodedata.normalize("NFD", lowered)
    ascii_only = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only)).strip("-")


def cell_text(cell) -> str:
    """Odwraca autokonwersje Excela (liczby, daty). Port z xlsx_to_csv.py."""
    v = cell.value
    if v is None:
        return ""
    if isinstance(v, datetime.datetime):
        fmt = (cell.number_format or "").lower()
        if "y" not in fmt:  # 'm-d' => wpisano "1-2", Excel zrobił datę
            return f"{v.month}-{v.day}"
        return v.date().isoformat()
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    if isinstance(v, int):
        return str(v)
    return str(v).strip()


def parse_tags(raw: str) -> list[str]:
    """Forma hashowa lub po przecinku, lowercase, dedup. Port z xlsx_to_csv.py."""
    if not raw:
        return []
    hashed = re.findall(r"#([^\s#,]+)", raw)
    parts = [t.strip(" .,;") for t in hashed] if hashed else [t.strip() for t in raw.split(",")]
    return list(dict.fromkeys(t.lower() for t in parts if t))


def cites_letter(text: str) -> bool:
    """Wykrywa jawne cytowanie litery w wyjaśnieniu (wzorzec wąski, bez fałszywych alarmów)."""
    if not text:
        return False
    return bool(
        re.search(r"\bOdpowiedź [A-D]\b", text)
        or re.search(r"\b[A-D] jest (poprawn|nieprawidłow|błędn)", text)
    )


def build_section_meta(section: dict) -> dict:
    topics = []
    for t in section["topics"]:
        count = sum(1 for q in section["questions"] if q["topic"] == t["title"])
        topics.append({"slug": t["slug"], "title": t["title"], "questionCount": count})
    return {
        "id": section["id"],
        "slug": slugify(section["title"]),
        "title": section["title"],
        "questionCount": len(section["questions"]),
        "file": f"sections/{section['id']}.json",
        "topics": topics,
    }


def main() -> None:
    import openpyxl  # tylko generacja potrzebuje xlsx; testy czystych funkcji (Task 1) nie

    if len(sys.argv) < 2:
        sys.exit("Użycie: python3 scripts/generate_quiz_data.py <ścieżka.xlsx>")
    xlsx_path = Path(sys.argv[1])
    wb = openpyxl.load_workbook(xlsx_path)  # bez data_only: number_format potrzebny
    struktura = wb["Struktura"]
    sheets = [s for s in wb.sheetnames if s != "Struktura"]

    # Struktura: (numer, dział, temat) — czytamy aż do pustego wiersza (bez hardkodu liczby).
    meta = []
    r = 1
    while True:
        num = struktura.cell(r, 1).value
        if num is None or str(num).strip() == "":
            break
        meta.append((int(num), cell_text(struktura.cell(r, 2)), cell_text(struktura.cell(r, 3))))
        r += 1
    if len(meta) != len(sheets):
        sys.exit(f"Niezgodność: {len(meta)} wierszy Struktury vs {len(sheets)} arkuszy pytań")

    errors: list[str] = []
    letter_warnings: list[str] = []
    sections_by_id: dict[int, dict] = {}

    for (section_no, section_name, topic), sheet in zip(meta, sheets):
        ws = wb[sheet]
        topic_slug = slugify(topic)
        section = sections_by_id.setdefault(
            section_no, {"id": section_no, "title": section_name, "topics": [], "questions": []}
        )
        section["topics"].append({"slug": topic_slug, "title": topic})

        for row in range(2, ws.max_row + 1):
            cells = [ws.cell(row, c) for c in range(1, 10)]
            vals = [cell_text(c) for c in cells]
            if not any(vals):
                continue  # pusty wiersz
            _, question, a, b, c_, d, correct, explanation, tags = vals
            qid = f"{section_no}-{topic_slug}-{row}"

            if question == "Pytanie" and a == "A":
                continue  # powtórzony nagłówek (jak w xlsx_to_csv.py)
            if question and not any([a, b, c_, d]):
                continue  # wiersz-separator / tytuł bloku (jak w xlsx_to_csv.py)
            if not all([question, a, b, c_, d]):
                errors.append(f"[{qid}] niekompletne pytanie")
                continue
            if correct.upper() not in LETTER_TO_INDEX:
                errors.append(f"[{qid}] nieprawidłowa Poprawna={correct!r}")
                continue
            if cites_letter(explanation):
                letter_warnings.append(qid)

            section["questions"].append({
                "id": qid,
                "section": section_name,
                "topic": topic,
                "question": question,
                "options": [a, b, c_, d],
                "correctIndex": LETTER_TO_INDEX[correct.upper()],
                "explanation": explanation,
                "tags": parse_tags(tags),
            })

    if errors:
        print(f"WALIDACJA NIEUDANA — {len(errors)} błędów:", file=sys.stderr)
        for e in errors[:50]:
            print("  " + e, file=sys.stderr)
        if len(errors) > 50:
            print(f"  ...i {len(errors) - 50} więcej", file=sys.stderr)
        sys.exit(1)

    sections = [sections_by_id[k] for k in sorted(sections_by_id)]
    manifest = {
        "generatedFrom": xlsx_path.name,
        "totalQuestions": sum(len(s["questions"]) for s in sections),
        "sections": [build_section_meta(s) for s in sections],
    }

    sections_dir = OUT_DIR / "sections"
    if sections_dir.exists():
        shutil.rmtree(sections_dir)  # usuń osierocone pliki działów z poprzednich importów
    sections_dir.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "index.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for s in sections:
        data = {"id": s["id"], "title": s["title"], "questions": s["questions"]}
        (sections_dir / f"{s['id']}.json").write_text(
            json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    total_topics = sum(len(s["topics"]) for s in sections)
    print(f"OK: {manifest['totalQuestions']} pytań, {len(sections)} działów, {total_topics} tematów")
    if letter_warnings:
        print(
            f"OSTRZEŻENIE: {len(letter_warnings)} wyjaśnień cytuje litery "
            f"(przepisz — spec sekcja 6). Np. {', '.join(letter_warnings[:5])}"
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Uruchom test — ma przejść**

Run: `python3 scripts/test_generate_quiz_data.py`
Expected: PASS — `OK test_cites_letter`, `OK test_parse_tags`, `OK test_slugify`, `Wszystkie testy przeszły (3)`.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_quiz_data.py scripts/test_generate_quiz_data.py
git commit -m "feat: python generator with tested pure functions"
```

---

## Task 2: Uruchomienie na realnych danych i weryfikacja

**Files:**
- Create (generated): `public/data/index.json`, `public/data/sections/1.json` … `18.json`

- [ ] **Step 1: Uruchom generator**

Run:
```bash
bun run data:generate data/neuro_questions.xlsx
```
Expected: `OK: 3389 pytań, 18 działów, 106 tematów` oraz OSTRZEŻENIE o ~936 wyjaśnieniach z literami (spodziewane przed przepisaniem).

- [ ] **Step 2: Zweryfikuj manifest**

Run:
```bash
python3 -c "import json; m=json.load(open('public/data/index.json')); print('działów', len(m['sections']), 'pytań', m['totalQuestions']); print('suma', sum(s['questionCount'] for s in m['sections'])); print('id', [s['id'] for s in m['sections']])"
```
Expected: `działów 18 pytań 3389`, suma równa 3389, id `[1, 2, ..., 18]`.

- [ ] **Step 3: Zweryfikuj kształt pytania i naprawę rozjazdu 180**

Run:
```bash
python3 -c "import json; m=json.load(open('public/data/index.json')); kres=[s for s in m['sections'] if s['title']=='Kresomózgowie'][0]; print('Kresomózgowie tematów', len(kres['topics']), 'pytań', kres['questionCount']); czu=[s for s in m['sections'] if s['title']=='Układ czuciowy'][0]; print('Układ czuciowy tematy:', ' | '.join(t['title'] for t in czu['topics'])); s1=json.load(open('public/data/sections/1.json')); q=s1['questions'][0]; print('klucze pytania:', ','.join(q.keys())); print('correctIndex', q['correctIndex'], type(q['correctIndex']).__name__, '| opcji', len(q['options']), '| tagi', q['tags'])"
```
Expected: „Kresomózgowie" ma **8 tematów, 240 pytań**; „Układ czuciowy" zawiera „Czucie powierzchniowe" (nie „powierzchowne"); pytanie ma klucze `id,section,topic,question,options,correctIndex,explanation,tags`; `correctIndex` to `int`; 4 opcje; tagi jako lista lowercase. Potwierdza to naprawę rozjazdu 180 pytań.

- [ ] **Step 4: Commit wygenerowanych danych**

```bash
git add public/data/index.json public/data/sections/
git commit -m "chore: generate quiz data from xlsx (3389 questions, 18 sections)"
```

---

## Task 3: Schemat zod (kontrakt strony) i typy

**Files:**
- Create: `src/lib/quiz-data.ts`

- [ ] **Step 1: Zdefiniuj schematy zod i typy**

```ts
import { z } from "zod";

// Kontrakt danych między generatorem (Python) a aplikacją (TS).
// Typy wyprowadzone przez z.infer — jedno źródło prawdy dla kształtu.

export const questionSchema = z.object({
  id: z.string(),
  section: z.string(),
  topic: z.string(),
  question: z.string().min(1),
  options: z.tuple([z.string(), z.string(), z.string(), z.string()]),
  correctIndex: z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3)]),
  explanation: z.string(),
  tags: z.array(z.string()),
});
export type Question = z.infer<typeof questionSchema>;

export const topicMetaSchema = z.object({
  slug: z.string(),
  title: z.string(),
  questionCount: z.number().int().nonnegative(),
});
export type TopicMeta = z.infer<typeof topicMetaSchema>;

export const sectionMetaSchema = z.object({
  id: z.number().int(),
  slug: z.string(),
  title: z.string(),
  questionCount: z.number().int().nonnegative(),
  file: z.string(),
  topics: z.array(topicMetaSchema),
});
export type SectionMeta = z.infer<typeof sectionMetaSchema>;

export const manifestSchema = z.object({
  generatedFrom: z.string(),
  totalQuestions: z.number().int().nonnegative(),
  sections: z.array(sectionMetaSchema),
});
export type Manifest = z.infer<typeof manifestSchema>;

export const sectionDataSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  questions: z.array(questionSchema),
});
export type SectionData = z.infer<typeof sectionDataSchema>;
```

- [ ] **Step 2: Sprawdź kompilację**

Run: `bunx tsc --noEmit`
Expected: brak błędów dotyczących `src/lib/quiz-data.ts`.

- [ ] **Step 3: Commit**

```bash
git add src/lib/quiz-data.ts
git commit -m "feat: zod schemas and types for quiz data contract"
```

---

## Task 4: Test zgodności — wygenerowany JSON vs schemat zod

**Files:**
- Test: `src/lib/quiz-data.test.ts`

Ten test jest bramką łapiącą rozjazd Python↔TS: jeśli generator (Python) wypluje JSON niezgodny z tym, czego oczekuje strona (`zod`), test pada.

- [ ] **Step 1: Napisz test**

```ts
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { manifestSchema, sectionDataSchema } from "./quiz-data";

function loadJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf-8"));
}

describe("wygenerowane dane spełniają schemat zod", () => {
  it("index.json parsuje się przez manifestSchema", () => {
    const manifest = manifestSchema.parse(loadJson("public/data/index.json"));
    expect(manifest.sections.length).toBeGreaterThan(0);
    const sumaZLicznikow = manifest.sections.reduce((n, s) => n + s.questionCount, 0);
    expect(manifest.totalQuestions).toBe(sumaZLicznikow);
  });

  it("każdy plik działu parsuje się i ma zgodną liczbę pytań", () => {
    const manifest = manifestSchema.parse(loadJson("public/data/index.json"));
    for (const section of manifest.sections) {
      const data = sectionDataSchema.parse(loadJson(`public/data/${section.file}`));
      expect(data.questions.length).toBe(section.questionCount);
      expect(data.id).toBe(section.id);
    }
  });
});
```

- [ ] **Step 2: Uruchom test — ma przejść (dane już wygenerowane w Task 2)**

Run: `bunx vitest run src/lib/quiz-data.test.ts`
Expected: PASS (2 testy). Jeśli padnie — generator wyprodukował JSON niezgodny ze schematem; to jest właśnie sygnał rozjazdu do naprawy, nie fałszywy alarm.

- [ ] **Step 3: Uruchom pełny zestaw testów**

Run: `bun run test`
Expected: PASS — testy vitest przechodzą. (Testy Pythona uruchamia się osobno: `python3 scripts/test_generate_quiz_data.py`.)

- [ ] **Step 4: Commit**

```bash
git add src/lib/quiz-data.test.ts
git commit -m "test: validate generated JSON against zod schema"
```

---

## Self-Review (wykonane przy pisaniu planu)

- **Pokrycie spec:** sekcja 3 (generator = narzędzie admina w Pythonie; app waliduje zod) → Taski 1, 3, 4. Sekcja 4b (rozszerzenie xlsx_to_csv.py, wyjście do public/data/, walidacja jako bramka, ostrzeżenie o literach) → Taski 1, 2. Sekcja 4b (druga bramka zod) → Taski 3, 4. Naprawa rozjazdu 180 → weryfikacja w Task 2 krok 3. Sekcja 6 (przepisanie wyjaśnień) i sekcja 7 (aplikacja) — świadomie POZA tym planem (osobna operacja + Plan 2).
- **Typy/nazwy spójne:** funkcje Pythona (`slugify`, `parse_tags`, `cell_text`, `cites_letter`, `build_section_meta`, `main`) identyczne w implementacji, teście i imporcie. Schematy zod (`questionSchema`, `manifestSchema`, `sectionDataSchema`, `sectionMetaSchema`, `topicMetaSchema`) spójne między definicją (Task 3) a użyciem w teście (Task 4). Kształt JSON generatora (klucze `id, section, topic, question, options, correctIndex, explanation, tags`; manifest `generatedFrom, totalQuestions, sections`) dokładnie odpowiada schematom zod.
- **Brak placeholderów:** każdy krok kodu ma pełny kod; komendy z oczekiwanym wyjściem.
- **Higiena wdrożenia (z przeglądu):** zależność `openpyxl` zadeklarowana w `requirements.txt` i instalowana w Task 0 (fresh env by padał); `import openpyxl` przeniesiony do `main()`, więc testy czystych funkcji (Task 1) go nie wymagają; kanoniczne źródło xlsx ustalone w repo (Task 0 Step 5), by uniknąć dryfu dwóch kopii; generator czyści `public/data/sections/` przed zapisem (`shutil.rmtree`), by nie zostawiać osieroconych plików działów po zmianie taksonomii. Weryfikacje w danych: id `(section+slug+row)` — 0 kolizji na 3389; 0 pustych `question`/opcji → dane spełniają `zod`.

## Uwaga o kolejności z Planem 2

Plan 2 (przełączenie aplikacji) zależy od kontraktu z Task 3 (`src/lib/quiz-data.ts`) i formatu plików z Task 2. Po wykonaniu tego planu format `index.json` i `sections/<id>.json` jest zamrożony i zwalidowany, a Plan 2 buduje na nim.
