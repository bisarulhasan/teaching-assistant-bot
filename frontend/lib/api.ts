const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ClassOption = {
  year: number;
  subject: string;
  course: string;
};

export type Source = {
  file: string;
  page: number;
  year: number;
  subject: string;
  course: string;
  chapter: number;
  chapter_title: string;
  section: string;
  label: string;
};

export type AskResponse = {
  answer: string;
  sources: Source[];
  is_supported: boolean | null;
  confidence: string | null;
};

export async function fetchCatalog(): Promise<ClassOption[]> {
  const res = await fetch(`${BASE}/catalog`);
  if (!res.ok) throw new Error(`catalog failed (${res.status})`);
  const data = await res.json();
  return data.catalog ?? [];
}

export async function ask(
  question: string,
  cls: ClassOption,
): Promise<AskResponse> {
  const res = await fetch(`${BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, ...cls }),
  });
  if (!res.ok) throw new Error(`ask failed (${res.status})`);
  return res.json();
}
