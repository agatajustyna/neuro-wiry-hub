import { describe, it, expect } from "vitest";
import { shuffle, shuffleOptions, buildPool } from "./quiz-pool";
import type { Question, SectionData } from "./quiz-data";

function q(id: string, correct: 0 | 1 | 2 | 3): Question {
  return {
    id,
    section: "S",
    topic: "T",
    question: "Q?",
    options: [`${id}-o0`, `${id}-o1`, `${id}-o2`, `${id}-o3`],
    correctIndex: correct,
    explanation: "",
    tags: [],
  };
}
function section(id: number, n: number): SectionData {
  return {
    id,
    title: `S${id}`,
    questions: Array.from({ length: n }, (_, i) => q(`${id}-t-${i}`, (i % 4) as 0 | 1 | 2 | 3)),
  };
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
      const original = q("x", 2); // poprawna = "x-o2"
      const r = shuffleOptions(original, mulberry32(seed));
      expect(r.options[r.correctIndex]).toBe("x-o2");
      expect([...r.options].sort()).toEqual(["x-o0", "x-o1", "x-o2", "x-o3"]);
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
  it("każde pytanie w puli ma zachowaną poprawną treść i zestaw opcji po losowaniu", () => {
    const sec = section(1, 8);
    const byId = new Map(sec.questions.map((orig) => [orig.id, orig]));
    const pool = buildPool([sec], "all", mulberry32(3));
    expect(pool).toHaveLength(8);
    for (const item of pool) {
      const orig = byId.get(item.id)!;
      expect(item.options[item.correctIndex]).toBe(orig.options[orig.correctIndex]);
      expect([...item.options].sort()).toEqual([...orig.options].sort());
    }
  });
  it("zwraca pustą pulę, gdy brak działów", () => {
    expect(buildPool([], 10)).toEqual([]);
  });
  it("przeplata pytania z różnych działów zamiast układać je blokowo (dział po dziale)", () => {
    const pool = buildPool([section(1, 5), section(2, 5)], "all", mulberry32(0));
    const sectionIds = pool.map((question) => question.id.split("-")[0]);
    // Nie jest to blok: najpierw cały dział 1, potem cały dział 2 (ani odwrotnie).
    expect(sectionIds).not.toEqual(["1", "1", "1", "1", "1", "2", "2", "2", "2", "2"]);
    expect(sectionIds).not.toEqual(["2", "2", "2", "2", "2", "1", "1", "1", "1", "1"]);
    // W pierwszych 4 elementach obecne są pytania z obu działów — realny przeplot.
    const firstFour = new Set(sectionIds.slice(0, 4));
    expect(firstFour.has("1")).toBe(true);
    expect(firstFour.has("2")).toBe(true);
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
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
