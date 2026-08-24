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
