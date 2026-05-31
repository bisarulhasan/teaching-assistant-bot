"use client";

import { useMemo, useState } from "react";
import type { ClassOption } from "@/lib/api";
import Mascot from "./Mascot";

const uniq = <T,>(xs: T[]) => Array.from(new Set(xs));

export default function ClassPicker({
  catalog,
  onPick,
}: {
  catalog: ClassOption[];
  onPick: (c: ClassOption) => void;
}) {
  const [year, setYear] = useState<number | null>(null);
  const [subject, setSubject] = useState<string | null>(null);

  const years = useMemo(
    () => uniq(catalog.map((c) => c.year)).sort((a, b) => a - b),
    [catalog],
  );
  const subjects = useMemo(
    () => uniq(catalog.filter((c) => c.year === year).map((c) => c.subject)).sort(),
    [catalog, year],
  );
  const courses = useMemo(
    () =>
      uniq(
        catalog
          .filter((c) => c.year === year && c.subject === subject)
          .map((c) => c.course),
      ).sort(),
    [catalog, year, subject],
  );

  const step = year === null ? 0 : subject === null ? 1 : 2;
  const prompts = ["Which year are you in?", "Pick your subject", "Which course?"];

  return (
    <div className="mx-auto flex min-h-dvh max-w-2xl flex-col items-center justify-center px-6 py-16 text-center">
      <div className="animate-rise" style={{ animationDelay: "40ms" }}>
        <Mascot size={120} bob />
      </div>

      <h1
        className="mt-6 font-[family-name:var(--font-display)] text-5xl font-light tracking-tight text-ink animate-rise sm:text-6xl"
        style={{ animationDelay: "120ms", fontFeatureSettings: '"ss01"' }}
      >
        Hi, I&rsquo;m Noor.
      </h1>
      <p
        className="mt-3 max-w-md text-lg text-ink-soft animate-rise"
        style={{ animationDelay: "200ms" }}
      >
        I answer straight from <em>your</em> textbooks — and I always show you the
        exact page. First, tell me your class.
      </p>

      {/* breadcrumb of choices made */}
      <div className="mt-8 flex flex-wrap items-center justify-center gap-2 text-sm">
        {year !== null && <Crumb label={`Year ${year}`} onClick={() => { setYear(null); setSubject(null); }} />}
        {subject !== null && <Crumb label={subject} onClick={() => setSubject(null)} />}
      </div>

      <p
        key={step}
        className="mt-6 font-[family-name:var(--font-display)] text-2xl font-light text-ink animate-pop"
      >
        {prompts[step]}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {step === 0 &&
          years.map((y, i) => (
            <Choice key={y} i={i} onClick={() => setYear(y)}>
              Year {y}
            </Choice>
          ))}
        {step === 1 &&
          subjects.map((s, i) => (
            <Choice key={s} i={i} onClick={() => setSubject(s)}>
              {s}
            </Choice>
          ))}
        {step === 2 &&
          courses.map((c, i) => (
            <Choice
              key={c}
              i={i}
              onClick={() => onPick({ year: year!, subject: subject!, course: c })}
            >
              {c}
            </Choice>
          ))}
      </div>

      <p className="fixed inset-x-0 bottom-5 text-center text-xs text-ink-soft/60">
        Made with <span className="text-coral">♥</span> by Bisar
      </p>
    </div>
  );
}

function Choice({
  children,
  onClick,
  i,
}: {
  children: React.ReactNode;
  onClick: () => void;
  i: number;
}) {
  return (
    <button
      onClick={onClick}
      data-choice
      className="animate-pop rounded-[var(--radius-blob)] border-2 border-ink/10 bg-white/70 px-7 py-4 text-lg font-bold text-ink shadow-[0_4px_0_rgba(43,42,38,0.10)] transition-all hover:-translate-y-0.5 hover:border-teal hover:bg-white hover:shadow-[0_6px_0_var(--color-teal-deep)] active:translate-y-0.5 active:shadow-[0_2px_0_var(--color-teal-deep)]"
      style={{ animationDelay: `${i * 60}ms` }}
    >
      {children}
    </button>
  );
}

function Crumb({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group inline-flex items-center gap-1.5 rounded-full bg-teal/12 px-3 py-1 font-bold text-teal-deep transition-colors hover:bg-coral/15 hover:text-coral-deep"
    >
      {label}
      <span className="text-xs opacity-60 group-hover:opacity-100">✕</span>
    </button>
  );
}
