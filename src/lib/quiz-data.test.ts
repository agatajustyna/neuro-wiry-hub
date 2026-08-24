import { describe, it, expect, afterEach } from "vitest";
import { readFileSync } from "node:fs";
import { manifestSchema, sectionDataSchema, fetchManifest, fetchSection } from "./quiz-data";

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

describe("fetchManifest / fetchSection", () => {
  const realFetch = globalThis.fetch;
  afterEach(() => {
    globalThis.fetch = realFetch;
  });

  it("fetchManifest waliduje odpowiedź schematem", async () => {
    const manifest = {
      generatedFrom: "x.xlsx",
      totalQuestions: 1,
      sections: [
        { id: 1, slug: "a", title: "A", questionCount: 1, file: "sections/1.json", topics: [] },
      ],
    };
    globalThis.fetch = (async () =>
      new Response(JSON.stringify(manifest), { status: 200 })) as typeof fetch;
    const m = await fetchManifest();
    expect(m.totalQuestions).toBe(1);
    expect(m.sections[0].file).toBe("sections/1.json");
  });

  it("fetchManifest rzuca przy błędzie HTTP", async () => {
    globalThis.fetch = (async () => new Response("nope", { status: 404 })) as typeof fetch;
    await expect(fetchManifest()).rejects.toThrow();
  });

  it("fetchSection waliduje i zwraca dane działu", async () => {
    const data = {
      id: 1,
      title: "A",
      questions: [
        {
          id: "1-a-2",
          section: "A",
          topic: "T",
          question: "Q?",
          options: ["a", "b", "c", "d"],
          correctIndex: 0,
          explanation: "",
          tags: [],
        },
      ],
    };
    globalThis.fetch = (async () =>
      new Response(JSON.stringify(data), { status: 200 })) as typeof fetch;
    const s = await fetchSection("sections/1.json");
    expect(s.questions).toHaveLength(1);
    expect(s.questions[0].correctIndex).toBe(0);
  });
});
