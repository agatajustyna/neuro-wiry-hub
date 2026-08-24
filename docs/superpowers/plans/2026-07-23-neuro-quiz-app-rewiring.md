# Neuro Quiz — Przełączenie aplikacji na dane (Plan 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Przełączyć aplikację z 10 mockowych pytań i zaszytej taksonomii na realne dane (`public/data/*.json` z Planu 1): manifest napędza ekran startowy z wielokrotnym wyborem działów, quiz buduje przemieszaną pulę z wybranych działów z losowaną kolejnością odpowiedzi.

**Architecture:** Dane wczytywane w runtime z `/data/index.json` + `/data/sections/<id>.json` przez `useQuery` (`@tanstack/react-query`) PO STRONIE KLIENTA — nie przez loadery tras, bo loadery biegną pod SSR, gdzie relatywny `fetch("/data/...")` rzuca (Node fetch wymaga absolutnego URL). Odpowiedzi walidowane schematami `zod` z `src/lib/quiz-data.ts` (Plan 1). Czysta logika budowy puli (merge działów, przemieszanie pytań, losowanie opcji z przeliczeniem indeksu poprawnej) w osobnym module testowanym vitest. Zaszyta `categories.ts` i 18 statycznych tras usunięte; zostają ekran startowy + trasa quizu.

**Tech Stack:** TanStack Start (SSR, React 19), TanStack Router (routing plikowy, `validateSearch`, `Route.useSearch`), `@tanstack/react-query` (`useQuery`, QueryClient wpięty w kontekst routera), zod, Tailwind 4, shadcn/ui, vitest, bun.

## Global Constraints

- Liczba pytań to **łączna z całej puli** wybranych działów (NIE per dział). Opcje selektora: **10 / 20 / 30 / 50 / wszystkie**.
- Pytania z wielu zaznaczonych działów są **przemieszane** (przeplatane), nie blokami.
- Kolejność odpowiedzi A–D jest **losowana per pytanie**; indeks poprawnej odpowiedzi musi być przeliczony na nową pozycję (poprawna treść zostaje poprawna).
- **Bez zapamiętywania między sesjami** — brak localStorage, brak kont. „Popraw błędne" działa tylko w obrębie sesji.
- **Tagi zostają w danych, ale NIE w UI.**
- Taksonomia (działy) pochodzi z manifestu — **zero list kategorii ani liczby „18" w kodzie**.
- Dane pod `/data/index.json` i `/data/sections/<id>.json` (serwowane z `public/`).
- Kontrakt danych: typy i schematy w `src/lib/quiz-data.ts` (`Manifest`, `SectionData`, `Question`, `manifestSchema`, `sectionDataSchema`). `Question` = `{ id, section, topic, question, options:[4], correctIndex:0|1|2|3, explanation, tags }`.
- Limit długości linii: 200 znaków.

**Poza zakresem (osobny Plan 3):** konfiguracja deployu Netlify (`@netlify/vite-plugin-tanstack-start`, `netlify.toml`, pogodzenie z Nitro z wrappera Lovable) — wymaga realnego buildu do rozstrzygnięcia, niezależna od kodu aplikacji.

---

## Struktura plików

- `src/lib/quiz-data.ts` (modyfikacja) — dodać `fetchManifest()`, `fetchSection(file)` z walidacją zod.
- `src/lib/quiz-pool.ts` (nowy) — czyste funkcje: `shuffle`, `shuffleOptions`, `buildPool`.
- `src/lib/quiz-pool.test.ts` (nowy) — testy vitest czystych funkcji.
- `src/lib/quiz-data.test.ts` (modyfikacja) — dodać testy `fetchManifest`/`fetchSection`.
- `src/components/TestSettings.tsx` (przepisanie) — wielokrotny wybór działów z manifestu + selektor liczby + „zaznacz wszystkie" → nawigacja do `/quiz` z search params. Bez tagów.
- `src/routes/index.tsx` (modyfikacja) — `useQuery(fetchManifest)` po stronie klienta, render `TestSettings` z działami z manifestu.
- `src/routes/quiz.tsx` (modyfikacja) — `validateSearch` + budowa puli przez `useQuery` (client-side) + strażnik pustej puli; `QuizPage` na realnym `Question`.
- `src/components/Breadcrumbs.tsx` (przepisanie) — bez `categories.ts` (Strona główna / Quiz).
- `src/routes/sitemap[.]xml.ts` (modyfikacja) — bez `categories.ts` (`/` + `/quiz`).
- USUNĄĆ: `src/lib/categories.ts`, `src/lib/mock-questions.ts`, `src/components/CategoryPage.tsx`, `src/routes/$category.$subcategory.tsx`, 18 plików statycznych tras działów (`ogolne.tsx`, `kresomozgowie.tsx`, `drogi-nerwowe.tsx`, `istota-biala.tsx`, `jadra-podstawy.tsx`, `komory-mozgu.tsx`, `miedzymozgowie.tsx`, `mozdzek.tsx`, `mozgowie-i-rdzen-nerwowy.tsx`, `nerwy-czaszkowe.tsx`, `pien-mozgu.tsx`, `rdzen-kregowy.tsx`, `uklad-czuciowy.tsx`, `uklad-limbiczny.tsx`, `uklad-nerwowy-autonomiczny.tsx`, `uklad-pozapiramidowy.tsx`, `uklad-ruchowy.tsx`, `zmysly.tsx`).

---

## Task 1: Wczytywanie danych z walidacją zod

**Files:**
- Modify: `src/lib/quiz-data.ts` (dopisać na końcu)
- Test: `src/lib/quiz-data.test.ts` (dopisać)

**Interfaces:**
- Consumes: `manifestSchema`, `sectionDataSchema`, typy `Manifest`, `SectionData` z `src/lib/quiz-data.ts` (Plan 1).
- Produces: `fetchManifest(): Promise<Manifest>`, `fetchSection(file: string): Promise<SectionData>`.

- [ ] **Step 1: Napisz testy (dopisz do `src/lib/quiz-data.test.ts`)**

```ts
import { fetchManifest, fetchSection } from "./quiz-data";

describe("fetchManifest / fetchSection", () => {
  const realFetch = globalThis.fetch;
  afterEach(() => { globalThis.fetch = realFetch; });

  it("fetchManifest waliduje odpowiedź schematem", async () => {
    const manifest = { generatedFrom: "x.xlsx", totalQuestions: 1, sections: [
      { id: 1, slug: "a", title: "A", questionCount: 1, file: "sections/1.json", topics: [] },
    ] };
    globalThis.fetch = (async () => new Response(JSON.stringify(manifest), { status: 200 })) as typeof fetch;
    const m = await fetchManifest();
    expect(m.totalQuestions).toBe(1);
    expect(m.sections[0].file).toBe("sections/1.json");
  });

  it("fetchManifest rzuca przy błędzie HTTP", async () => {
    globalThis.fetch = (async () => new Response("nope", { status: 404 })) as typeof fetch;
    await expect(fetchManifest()).rejects.toThrow();
  });

  it("fetchSection waliduje i zwraca dane działu", async () => {
    const data = { id: 1, title: "A", questions: [
      { id: "1-a-2", section: "A", topic: "T", question: "Q?", options: ["a", "b", "c", "d"], correctIndex: 0, explanation: "", tags: [] },
    ] };
    globalThis.fetch = (async () => new Response(JSON.stringify(data), { status: 200 })) as typeof fetch;
    const s = await fetchSection("sections/1.json");
    expect(s.questions).toHaveLength(1);
    expect(s.questions[0].correctIndex).toBe(0);
  });
});
```

- [ ] **Step 2: Uruchom test — ma nie przejść**

Run: `bunx vitest run src/lib/quiz-data.test.ts`
Expected: FAIL — `fetchManifest is not a function` / brak eksportu.

- [ ] **Step 3: Zaimplementuj (dopisz na końcu `src/lib/quiz-data.ts`)**

```ts
export async function fetchManifest(): Promise<Manifest> {
  const res = await fetch("/data/index.json");
  if (!res.ok) throw new Error(`Nie udało się wczytać manifestu (HTTP ${res.status})`);
  return manifestSchema.parse(await res.json());
}

export async function fetchSection(file: string): Promise<SectionData> {
  const res = await fetch(`/data/${file}`);
  if (!res.ok) throw new Error(`Nie udało się wczytać działu ${file} (HTTP ${res.status})`);
  return sectionDataSchema.parse(await res.json());
}
```

- [ ] **Step 4: Uruchom test — ma przejść**

Run: `bunx vitest run src/lib/quiz-data.test.ts`
Expected: PASS (testy Planu 1 + 3 nowe).

- [ ] **Step 5: Commit**

```bash
git add src/lib/quiz-data.ts src/lib/quiz-data.test.ts
git commit -m "feat: fetch+validate manifest and section data"
```

---

## Task 2: Budowa puli quizu (przemieszanie + losowanie opcji)

**Files:**
- Create: `src/lib/quiz-pool.ts`
- Test: `src/lib/quiz-pool.test.ts`

**Interfaces:**
- Consumes: typy `Question`, `SectionData` z `src/lib/quiz-data.ts`.
- Produces: `shuffle<T>(arr, rng?): T[]`, `shuffleOptions(q: Question, rng?): Question`, `buildPool(sections: SectionData[], count: number | "all", rng?): Question[]`.

- [ ] **Step 1: Napisz testy**

```ts
import { describe, it, expect } from "vitest";
import { shuffle, shuffleOptions, buildPool } from "./quiz-pool";
import type { Question, SectionData } from "./quiz-data";

function q(id: string, correct: 0 | 1 | 2 | 3): Question {
  return { id, section: "S", topic: "T", question: "Q?", options: ["a", "b", "c", "d"], correctIndex: correct, explanation: "", tags: [] };
}
function section(id: number, n: number): SectionData {
  return { id, title: `S${id}`, questions: Array.from({ length: n }, (_, i) => q(`${id}-t-${i}`, (i % 4) as 0 | 1 | 2 | 3)) };
}

describe("shuffle", () => {
  it("zwraca permutację, nie mutuje wejścia", () => {
    const input = [1, 2, 3, 4, 5];
    const out = shuffle(input, seq([0.5, 0.1, 0.9, 0.3]));
    expect(out).toHaveLength(5);
    expect([...out].sort()).toEqual([1, 2, 3, 4, 5]);
    expect(input).toEqual([1, 2, 3, 4, 5]);
  });
});

describe("shuffleOptions", () => {
  it("zachowuje poprawną treść na nowym correctIndex (dla dowolnego rng)", () => {
    for (let seed = 0; seed < 20; seed++) {
      const original = q("x", 2); // poprawna = "c"
      const r = shuffleOptions(original, mulberry32(seed));
      expect(r.options[r.correctIndex]).toBe("c");
      expect([...r.options].sort()).toEqual(["a", "b", "c", "d"]);
    }
  });
});

describe("buildPool", () => {
  it("łączy działy i przycina do liczby łącznej", () => {
    const pool = buildPool([section(1, 30), section(2, 30)], 20, mulberry32(1));
    expect(pool).toHaveLength(20);
  });
  it("'all' zwraca wszystkie pytania z sumy działów", () => {
    const pool = buildPool([section(1, 30), section(2, 30)], "all", mulberry32(1));
    expect(pool).toHaveLength(60);
  });
  it("każde pytanie w puli ma zachowaną poprawną treść po losowaniu opcji", () => {
    const pool = buildPool([section(1, 8)], "all", mulberry32(3));
    for (const item of pool) {
      expect(["a", "b", "c", "d"]).toContain(item.options[item.correctIndex]);
      expect([...item.options].sort()).toEqual(["a", "b", "c", "d"]);
    }
  });
});

// deterministyczne rng do testów
function seq(values: number[]): () => number {
  let i = 0;
  return () => values[i++ % values.length];
}
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
```

- [ ] **Step 2: Uruchom test — ma nie przejść**

Run: `bunx vitest run src/lib/quiz-pool.test.ts`
Expected: FAIL — brak modułu `./quiz-pool`.

- [ ] **Step 3: Zaimplementuj `src/lib/quiz-pool.ts`**

```ts
import type { Question, SectionData } from "./quiz-data";

// Fisher-Yates z wstrzykiwanym rng (domyślnie Math.random) dla testowalności.
export function shuffle<T>(arr: readonly T[], rng: () => number = Math.random): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Losuje kolejność opcji i przelicza correctIndex na nową pozycję poprawnej treści.
export function shuffleOptions(question: Question, rng: () => number = Math.random): Question {
  const order = shuffle([0, 1, 2, 3], rng);
  const options = order.map((i) => question.options[i]) as [string, string, string, string];
  const correctIndex = order.indexOf(question.correctIndex) as 0 | 1 | 2 | 3;
  return { ...question, options, correctIndex };
}

// Buduje pulę: łączy działy, przemieszuje pytania, przycina do liczby łącznej, losuje opcje.
export function buildPool(
  sections: SectionData[],
  count: number | "all",
  rng: () => number = Math.random,
): Question[] {
  const merged = sections.flatMap((s) => s.questions);
  const shuffled = shuffle(merged, rng);
  const limited = count === "all" ? shuffled : shuffled.slice(0, count);
  return limited.map((question) => shuffleOptions(question, rng));
}
```

- [ ] **Step 4: Uruchom test — ma przejść**

Run: `bunx vitest run src/lib/quiz-pool.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/lib/quiz-pool.ts src/lib/quiz-pool.test.ts
git commit -m "feat: quiz pool builder with option shuffling"
```

---

## Task 3: Ekran startowy — wielokrotny wybór działów z manifestu

**Files:**
- Modify: `src/components/TestSettings.tsx` (przepisanie)
- Modify: `src/routes/index.tsx`

**Interfaces:**
- Consumes: `fetchManifest` (Task 1), typ `SectionMeta` z `src/lib/quiz-data.ts`.
- Produces: `TestSettings` przyjmuje `sections: SectionMeta[]`; nawiguje do `/quiz` z `search: { sections: number[], count: 10|20|30|50|"all" }` (kontrakt konsumowany w Task 4).

- [ ] **Step 1: Przepisz `src/components/TestSettings.tsx`**

Zastępuje atrapę tagów i martwy selektor. Wielokrotny wybór działów (checkboxy) + „zaznacz wszystkie" + selektor liczby, przycisk startu z realnymi search params.

```tsx
import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import type { SectionMeta } from "@/lib/quiz-data";

type Count = 10 | 20 | 30 | 50 | "all";
const COUNT_OPTIONS: { value: Count; label: string }[] = [
  { value: 10, label: "10" }, { value: 20, label: "20" }, { value: 30, label: "30" },
  { value: 50, label: "50" }, { value: "all", label: "Wszystkie" },
];

interface TestSettingsProps {
  sections: SectionMeta[];
}

export function TestSettings({ sections }: TestSettingsProps) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [count, setCount] = useState<Count>(30);

  const allSelected = selected.size === sections.length && sections.length > 0;
  const toggle = (id: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  const toggleAll = () =>
    setSelected(allSelected ? new Set() : new Set(sections.map((s) => s.id)));

  const totalSelected = sections.filter((s) => selected.has(s.id)).reduce((n, s) => n + s.questionCount, 0);

  const start = () => {
    if (selected.size === 0) return;
    navigate({ to: "/quiz", search: { sections: [...selected], count } });
  };

  return (
    <div className="mx-auto w-full max-w-2xl">
      <section className="mb-8 rounded-3xl border border-border/60 bg-card p-6 sm:p-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Działy</h2>
          <button
            type="button"
            onClick={toggleAll}
            className="text-sm font-medium text-primary transition-opacity hover:opacity-70"
          >
            {allSelected ? "Odznacz wszystkie" : "Zaznacz wszystkie"}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {sections.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => toggle(s.id)}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                selected.has(s.id)
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {s.title}
              <span className="text-xs opacity-70">{s.questionCount}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="mb-8 rounded-3xl border border-border/60 bg-card p-6 sm:p-8">
        <h2 className="text-lg font-semibold text-foreground">Liczba pytań (łącznie)</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {COUNT_OPTIONS.map((opt) => (
            <button
              key={String(opt.value)}
              type="button"
              onClick={() => setCount(opt.value)}
              className={`inline-flex items-center rounded-full px-4 py-2 text-sm font-medium transition-all ${
                count === opt.value
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-border/60 bg-card p-6 sm:p-8">
        <p className="text-sm text-muted-foreground">
          Wybrano {selected.size} {selected.size === 1 ? "dział" : "działów"} · {totalSelected} pytań dostępnych
        </p>
        <button
          type="button"
          onClick={start}
          disabled={selected.size === 0}
          className="mt-4 inline-flex w-full items-center justify-center rounded-full bg-primary px-6 py-4 text-base font-semibold text-primary-foreground transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Rozpocznij test
        </button>
      </section>
    </div>
  );
}
```

- [ ] **Step 2: Zmodyfikuj `src/routes/index.tsx`**

Wczytaj manifest PO STRONIE KLIENTA przez `useQuery` (nie loader trasy — loader biegnie pod SSR, gdzie relatywny `fetch("/data/...")` rzuca). `QueryClientProvider` jest już wpięty w `__root.tsx`, a `useQuery` domyślnie nie fetchuje podczas SSR (renderuje stan ładowania, pobiera po zamontowaniu na kliencie). Usuń import `categories` i sekcję kafelków kategorii. Cała treść pliku:

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Brain } from "lucide-react";
import { fetchManifest } from "@/lib/quiz-data";
import { TestSettings } from "@/components/TestSettings";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const { data: manifest, isLoading, error } = useQuery({
    queryKey: ["manifest"],
    queryFn: fetchManifest,
    staleTime: Infinity,
  });

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-foreground">Neuro Świry</span>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="px-4 pb-6 pt-16 sm:px-6 sm:pt-24">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-8 inline-flex h-20 w-20 items-center justify-center rounded-[var(--radius-2xl)] bg-primary/10">
              <Brain className="h-10 w-10 text-primary" />
            </div>
            <h1 className="text-5xl font-extrabold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
              Neuro <span className="text-primary">Świry</span>
            </h1>
            <p className="mt-6 text-base text-muted-foreground">
              Zaznacz działy, wybierz liczbę pytań i rozpocznij test.
            </p>
          </div>
        </section>

        <section className="px-4 pb-16 sm:px-6">
          <div className="mx-auto max-w-4xl">
            {isLoading && <p className="text-center text-muted-foreground">Wczytywanie działów…</p>}
            {(error || (!isLoading && !manifest)) && (
              <p className="text-center text-destructive">Nie udało się wczytać danych. Odśwież stronę.</p>
            )}
            {manifest && <TestSettings sections={manifest.sections} />}
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-6 text-center">
        <p className="text-sm text-muted-foreground">Neuro Świry — nauka neuroanatomii z pasją</p>
      </footer>
    </div>
  );
}
```

- [ ] **Step 3: Sprawdź typy i uruchom dev**

Run: `bunx tsc --noEmit 2>&1 | grep -E "index.tsx|TestSettings" || echo "brak błędów w naszych plikach"`
Expected: brak błędów w `index.tsx`/`TestSettings.tsx`. (Uwaga: `Breadcrumbs.tsx`, usuwane trasy i `categories.ts` mogą jeszcze zgłaszać błędy — porządkuje je Task 5; ignoruj je tutaj.)

- [ ] **Step 4: Commit**

```bash
git add src/components/TestSettings.tsx src/routes/index.tsx
git commit -m "feat: manifest-driven landing with multi-section select"
```

---

## Task 4: Trasa quizu — search params + budowa puli (client-side)

**Files:**
- Modify: `src/routes/quiz.tsx`

**Interfaces:**
- Consumes: `fetchManifest`, `fetchSection` (Task 1), `buildPool` (Task 2), typ `Question`; search params `{ sections: number[], count: 10|20|30|50|"all" }` (Task 3).
- Produces: quiz działający na realnej puli `Question[]`.

- [ ] **Step 1: Zmień nagłówek trasy w `src/routes/quiz.tsx`**

Zastąp linie 1-12 (importy + `createFileRoute` blok) tym. Dodaje `validateSearch` (zod). NIE ma loadera trasy — dane pobieramy po stronie klienta (loader pod SSR rzuca na relatywnym `fetch`):

```tsx
import { useCallback, useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Brain, Check, X } from "lucide-react";
import { z } from "zod";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { fetchManifest, fetchSection, type Question } from "@/lib/quiz-data";
import { buildPool } from "@/lib/quiz-pool";

const quizSearchSchema = z.object({
  sections: z.array(z.number().int()).min(1),
  count: z.union([z.literal(10), z.literal(20), z.literal(30), z.literal(50), z.literal("all")]),
});

export const Route = createFileRoute("/quiz")({
  validateSearch: (search) => quizSearchSchema.parse(search),
  component: QuizPage,
  head: () => ({ meta: [{ title: "Quiz — Neuro Świry" }] }),
});
```

- [ ] **Step 2: Zbuduj pulę po stronie klienta (`useQuery`) i podłącz do stanu**

W `QuizPage` zamień źródło pytań. Zastąp linię (dawniej `const [questions, setQuestions] = useState<QuizQuestion[]>(() => MOCK_QUESTIONS);`) tym — pula budowana z search params po stronie klienta (SSR-safe):

```tsx
  const { sections, count } = Route.useSearch();
  const { data: manifest } = useQuery({ queryKey: ["manifest"], queryFn: fetchManifest, staleTime: Infinity });
  const files = manifest?.sections.filter((s) => sections.includes(s.id)).map((s) => s.file) ?? [];
  const { data: pool, isLoading } = useQuery({
    queryKey: ["pool", sections, count],
    queryFn: async () => buildPool(await Promise.all(files.map(fetchSection)), count),
    enabled: !!manifest,
    staleTime: Infinity,
  });
  const [questions, setQuestions] = useState<Question[]>([]);
  useEffect(() => { if (pool) setQuestions(pool); }, [pool]);
```

`queryKey: ["manifest"]` jest współdzielony z ekranem startowym — react-query nie pobiera manifestu drugi raz. `buildPool` (z `Math.random`) biegnie tylko na kliencie → brak rozjazdu hydratacji SSR.

Zmień `restartAll` (dawniej `setQuestions(MOCK_QUESTIONS)`) na:

```tsx
  const restartAll = () => {
    if (pool) setQuestions(pool);
    setCurrentIdx(0);
    setSelected(null);
    setAnswers([]);
    setFinished(false);
  };
```

- [ ] **Step 3: Dodaj strażnik ładowania i pustej puli**

W `QuizPage`, po WSZYSTKICH hookach (`useCallback`/`useEffect`), tuż przed głównym `return (<div className="flex min-h-screen flex-col">`, wstaw:

```tsx
  if (isLoading || !pool) {
    return <QuizMessage text="Wczytywanie pytań…" />;
  }
  if (questions.length === 0) {
    return <QuizMessage text="Brak pytań dla wybranych działów." homeLink />;
  }
```

Dodaj mały komponent `QuizMessage` w tym pliku (poza `QuizPage`). `Link` i `ArrowLeft` są już importowane:

```tsx
function QuizMessage({ text, homeLink }: { text: string; homeLink?: boolean }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="text-lg text-muted-foreground">{text}</p>
      {homeLink && (
        <Link to="/" className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90">
          <ArrowLeft className="h-4 w-4" /> Wróć do wyboru działów
        </Link>
      )}
    </div>
  );
}
```

Strażnik chroni przed `?sections=[999]` (nieistniejące id przechodzą `validateSearch`, dają pustą pulę) i przed dostępem do `questions[currentIdx]` gdy pula pusta. Musi stać PO hookach (reguły hooków), a przed renderem `QuestionView`.

- [ ] **Step 4: Zamień `QuizQuestion` na `Question` i `answers` na `options`**

W całym pliku: typ `QuizQuestion` → `Question`. W `QuestionView` props type `question: QuizQuestion` → `question: Question`. Renderowanie wariantów odpowiedzi: `question.answers.map(...)` → `question.options.map(...)`. Etykieta kategorii nad pytaniem: zamień `{question.category}` na:

```tsx
        {question.section} › {question.topic}
```

- [ ] **Step 5: Sprawdź typy**

Run: `bunx tsc --noEmit 2>&1 | grep -E "quiz.tsx" || echo "brak błędów w quiz.tsx"`
Expected: brak błędów w `quiz.tsx` (poza ewentualnymi z `Breadcrumbs.tsx` — Task 5).

- [ ] **Step 6: Commit**

```bash
git add src/routes/quiz.tsx
git commit -m "feat: quiz builds real pool from search params (client-side useQuery)"
```

---

## Task 5: Usunięcie zaszytej taksonomii, martwych tras i zależności

**Files:**
- Delete: `src/lib/categories.ts`, `src/lib/mock-questions.ts`, `src/components/CategoryPage.tsx`, `src/routes/$category.$subcategory.tsx`, oraz 18 plików statycznych tras działów (lista w sekcji „Struktura plików").
- Modify: `src/components/Breadcrumbs.tsx`, `src/routes/sitemap[.]xml.ts`

**Interfaces:**
- Consumes: nic nowego.
- Produces: aplikacja bez `categories.ts`/`mock-questions.ts`; `routeTree.gen.ts` bez usuniętych tras (regenerowane automatycznie).

- [ ] **Step 1: Przepisz `src/components/Breadcrumbs.tsx` (bez categories)**

```tsx
import { Link, useLocation } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

export function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);

  const items: { label: string; href?: string; current: boolean }[] = [
    { label: "Strona główna", href: "/", current: segments.length === 0 },
  ];
  if (segments[0] === "quiz") {
    items.push({ label: "Quiz", current: true });
  }

  return (
    <nav aria-label="Breadcrumb" className="w-full border-b border-border/40 bg-background/80">
      <div className="mx-auto flex max-w-6xl items-center overflow-x-auto whitespace-nowrap px-4 py-2 sm:px-6">
        <ol className="flex items-center gap-1 text-xs text-muted-foreground">
          {items.map((item, index) => (
            <li key={index} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground/50" />}
              {item.current ? (
                <span className="font-medium text-foreground">{item.label}</span>
              ) : (
                <Link to={item.href!} className="transition-colors hover:text-foreground">
                  {item.label}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </div>
    </nav>
  );
}
```

- [ ] **Step 2: Zmodyfikuj `src/routes/sitemap[.]xml.ts` (bez categories)**

Zastąp import i budowę `entries`. Usuń `import { categories }`. Zmień tablicę `entries` na statyczne `/` + `/quiz`:

```ts
import { createFileRoute } from "@tanstack/react-router";

const BASE_URL = "https://neuro-swiry.lovable.app";

interface SitemapEntry {
  path: string;
  changefreq?: "always" | "hourly" | "daily" | "weekly" | "monthly" | "yearly" | "never";
  priority?: string;
}

export const Route = createFileRoute("/sitemap.xml")({
  server: {
    handlers: {
      GET: async () => {
        const entries: SitemapEntry[] = [
          { path: "/", changefreq: "weekly", priority: "1.0" },
          { path: "/quiz", changefreq: "weekly", priority: "0.8" },
        ];
        const urls = entries.map((e) =>
          [
            `  <url>`,
            `    <loc>${BASE_URL}${e.path}</loc>`,
            e.changefreq ? `    <changefreq>${e.changefreq}</changefreq>` : null,
            e.priority ? `    <priority>${e.priority}</priority>` : null,
            `  </url>`,
          ].filter(Boolean).join("\n"),
        );
        const xml = [
          `<?xml version="1.0" encoding="UTF-8"?>`,
          `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`,
          ...urls,
          `</urlset>`,
        ].join("\n");
        return new Response(xml, {
          headers: { "Content-Type": "application/xml", "Cache-Control": "public, max-age=3600" },
        });
      },
    },
  },
});
```

- [ ] **Step 3: Usuń martwe pliki**

Run:
```bash
git rm src/lib/categories.ts src/lib/mock-questions.ts src/components/CategoryPage.tsx \
  src/routes/'$category.$subcategory.tsx' \
  src/routes/ogolne.tsx src/routes/kresomozgowie.tsx src/routes/drogi-nerwowe.tsx \
  src/routes/istota-biala.tsx src/routes/jadra-podstawy.tsx src/routes/komory-mozgu.tsx \
  src/routes/miedzymozgowie.tsx src/routes/mozdzek.tsx src/routes/mozgowie-i-rdzen-nerwowy.tsx \
  src/routes/nerwy-czaszkowe.tsx src/routes/pien-mozgu.tsx src/routes/rdzen-kregowy.tsx \
  src/routes/uklad-czuciowy.tsx src/routes/uklad-limbiczny.tsx src/routes/uklad-nerwowy-autonomiczny.tsx \
  src/routes/uklad-pozapiramidowy.tsx src/routes/uklad-ruchowy.tsx src/routes/zmysly.tsx
```
Expected: 23 pliki usunięte (5 nie-tras + 18 tras działów). `$category.$subcategory.tsx` cudzysłowy ważne (znak `$`).

- [ ] **Step 4: Regeneruj routeTree i sprawdź typy całego repo**

Run: `bun run build 2>&1 | tail -20`
Expected: build się kończy sukcesem; `src/routeTree.gen.ts` zregenerowane bez usuniętych tras (plugin routera robi to podczas `vite build`). Jeśli build zgłosi błąd typu w innym pliku — napraw dangling import zanim przejdziesz dalej.

Run: `bunx tsc --noEmit 2>&1 | tail -20`
Expected: brak błędów o `@/lib/categories` ani `@/lib/mock-questions` (nikt ich już nie importuje).

- [ ] **Step 5: Uruchom pełny zestaw testów**

Run: `bun run test`
Expected: PASS — testy vitest (quiz-data, quiz-pool) przechodzą.
Run: `python3 scripts/test_generate_quiz_data.py`
Expected: PASS (potok danych nietknięty).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: drop hardcoded taxonomy, static routes, mocks; landing+quiz only"
```

---

## Self-Review (wykonane przy pisaniu planu)

- **Pokrycie spec:** sekcja 5 (ekran startowy multi-select, liczba łączna, przemieszanie) → Task 3, 2, 4. Sekcja 6 (losowanie odpowiedzi bezpieczne po przepisaniu wyjaśnień) → Task 2 (`shuffleOptions` z przeliczeniem correctIndex). Sekcja 7 (zdjęcie taksonomii, model pytania z zod, przekazanie zakresu, wielokrotny wybór, martwy selektor, tagi z UI, 18 tras, usunięcie mocków, naprawa martwego linku `$category`, sitemap, literówka `ogolne`) → Taski 3, 4, 5 (usunięcie plików eliminuje martwy link i literówkę). Sekcja 3 (walidacja zod przy wczytaniu) → Task 1. Sekcja 8 (deploy) → świadomie POZA (Plan 3).
- **Typy/nazwy spójne:** `fetchManifest`/`fetchSection` (Task 1) wołane przez `useQuery` w Task 3 (index) i Task 4 (quiz). `buildPool` (Task 2) użyty w Task 4. `SectionMeta` (Task 3 props) i `Question` (Task 4) z `quiz-data.ts`. Search params `{ sections: number[], count }` produkowane w Task 3 (`navigate`), walidowane w Task 4 (`quizSearchSchema` w `validateSearch`) i czytane przez `Route.useSearch()`. Pole `options` (nie `answers`), `correctIndex`, `section`/`topic` spójne z typem `Question` z Planu 1.
- **Brak placeholderów:** każdy krok kodu ma pełny kod; komendy z oczekiwanym wyjściem.

## Ryzyka do świadomości wykonawcy

- **Fetch po stronie klienta, NIE w loaderze trasy.** Zweryfikowane w przeglądzie: SSR jest aktywny (brak `ssr:false`), loadery tras biegną na serwerze, a Node global fetch rzuca na relatywnym URL (`fetch('/data/x.json')` → „Failed to parse URL"). Dlatego dane pobiera `useQuery` w komponentach (client-side) — `useQuery` domyślnie nie fetchuje podczas SSR, więc relatywny `/data/...` wykonuje się dopiero w przeglądarce. `QueryClientProvider` jest już wpięty w `__root.tsx`. Wykonawca potwierdza całą ścieżkę przez `bun run dev`: ekran startowy → wybór działów → quiz → wynik.
- **Serializacja search params — ZWERYFIKOWANA jako poprawna.** Domyślny parser routera to `parseSearchWith(JSON.parse)` (`@tanstack/router-core/.../searchParams.js`), router go nie nadpisuje. `sections=[1,2]` wraca jako tablica liczb, `count=30` jako liczba, `count=all` jako string `"all"` (JSON.parse rzuca → zostaje string) — dokładnie to, czego oczekuje `quizSearchSchema`. Żadna koercja nie jest potrzebna; schemat z Task 4 działa bez zmian.
- **Manifest fetchowany raz.** `useQuery({ queryKey: ["manifest"] })` na ekranie startowym i w quizie dzielą ten sam klucz — react-query deduplikuje, nie ma podwójnego pobrania.
- **`routeTree.gen.ts` jest generowany** — po usunięciu plików tras musi zostać przegenerowany przez `vite build`/`vite dev`. Nie edytuj go ręcznie.
- Po tym planie aplikacja działa lokalnie na realnych danych, ale **nie jest jeszcze wdrożona** — deploy Netlify to Plan 3.
