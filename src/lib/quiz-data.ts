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
