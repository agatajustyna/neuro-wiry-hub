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
