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
