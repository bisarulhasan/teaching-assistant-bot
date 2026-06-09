"use client";

import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { ask, type ClassOption, type Source } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import Mascot from "./Mascot";

type Msg = {
  id: number;
  role: "user" | "pip";
  text: string;
  sources?: Source[];
  confidence?: string | null;
  supported?: boolean | null;
  error?: boolean;
};

// Starters PREFILL the composer with a lead-in and focus it, so the student
// always names a topic — sending these as-is would give the bot no topic.
const STARTERS = [
  { label: "Explain a topic", lead: "Explain " },
  { label: "Worked example", lead: "Give me a worked example of " },
  { label: "Find a formula", lead: "What's the formula for " },
];

/** Strip the inline [Source: …] tags — we show sources as chips instead. */
function cleanAnswer(text: string): string {
  return text.replace(/\s*\[Source:[^\]]*\]/g, "").replace(/\n{3,}/g, "\n\n").trim();
}

/** Normalize the LLM's LaTeX delimiters to the $/$$ that remark-math expects.
 * Anchors on the reliably-balanced `aligned` blocks and wraps each in $$,
 * consuming any adjacent \[ \] — because a small model sometimes leaves those
 * unbalanced, which would otherwise break display-math pairing. */
function normalizeMath(text: string): string {
  return text
    // each aligned block -> a $$ display block, eating any adjacent \[ \]
    .replace(
      /(?:\\\[)?\s*(\\begin\{aligned\}[\s\S]*?\\end\{aligned\})\s*(?:\\\])?/g,
      (_, block) => `\n\n$$\n${block}\n$$\n\n`,
    )
    // remaining balanced single-line display \[ ... \] -> $$ ... $$
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, inner) => `\n$$${inner}$$\n`)
    // drop any stray unmatched \[ or \]
    .replace(/\\\[|\\\]/g, "")
    // inline \( ... \) -> $ ... $
    .replace(/\\\(/g, () => "$")
    .replace(/\\\)/g, () => "$");
}

export default function Chat({
  cls,
  onSwitchClass,
}: {
  cls: ClassOption;
  onSwitchClass: () => void;
}) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const idRef = useRef(0);

  function compose(lead: string) {
    setInput(lead);
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (el) {
        el.focus();
        el.setSelectionRange(lead.length, lead.length);
      }
    });
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(q: string) {
    const question = q.trim();
    if (!question || busy) return;
    const userMsg: Msg = { id: idRef.current++, role: "user", text: question };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);
    try {
      const res = await ask(question, cls);
      setMessages((m) => [
        ...m,
        {
          id: idRef.current++,
          role: "pip",
          text: cleanAnswer(res.answer),
          sources: res.sources,
          confidence: res.confidence,
          supported: res.is_supported,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: idRef.current++,
          role: "pip",
          text: "Hmm, I couldn't reach my brain just now. Check that the assistant is running and try again.",
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative z-10 mx-auto flex h-dvh max-w-3xl flex-col px-4">
      {/* Header */}
      <header className="flex items-center justify-between gap-3 py-4">
        <div className="flex items-center gap-3">
          <Mascot size={88} />
          <div className="leading-tight">
            <p className="font-[family-name:var(--font-display)] text-xl text-ink">Noor</p>
            <p className="text-xs text-ink-soft">Ask your textbook</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onSwitchClass}
            className="group flex items-center gap-2 rounded-full border-2 border-ink/10 bg-white/70 px-4 py-2 text-sm font-bold text-ink transition-colors hover:border-teal hover:text-teal-deep"
          >
            <span className="text-ink-soft group-hover:text-teal-deep">Year {cls.year}</span>
            {cls.subject}{cls.course ? ` · ${cls.course}` : ""}
            <span className="text-xs opacity-50">change</span>
          </button>
          <button
            onClick={() => supabase.auth.signOut()}
            title="Sign out"
            aria-label="Sign out"
            className="grid h-9 w-9 place-items-center rounded-full border-2 border-ink/10 bg-white/70 text-ink-soft transition-colors hover:border-coral hover:text-coral-deep"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto pb-4 pt-2">
        {messages.length === 0 && <EmptyState onCompose={compose} />}
        {messages.map((m) =>
          m.role === "user" ? (
            <UserBubble key={m.id} text={m.text} />
          ) : (
            <PipBubble key={m.id} msg={m} />
          ),
        )}
        {busy && <Typing />}
      </div>

      {/* Composer */}
      <div className="sticky bottom-0 z-10 pb-5 pt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="flex items-end gap-2 rounded-[var(--radius-blob)] border-2 border-ink/10 bg-white/85 p-2 shadow-[0_6px_0_rgba(43,42,38,0.08)] backdrop-blur transition-colors focus-within:border-teal"
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={1}
            placeholder={`Ask anything from Year ${cls.year} ${cls.subject} ${cls.course}…`}
            className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-ink outline-none placeholder:text-ink-soft/60"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            aria-label="Send"
            className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-coral text-white shadow-[0_3px_0_var(--color-coral-deep)] transition-all hover:-translate-y-0.5 hover:shadow-[0_5px_0_var(--color-coral-deep)] active:translate-y-0.5 active:shadow-none disabled:cursor-not-allowed disabled:opacity-40"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </form>
        <p className="mt-2 text-center text-xs text-ink-soft/70">
          Noor only answers from your textbooks. Always double-check with your teacher.
        </p>
        <p className="mt-1 text-center text-xs text-ink-soft/60">
          Made with <span className="text-coral">♥</span> by{" "}
          <a
            href="https://bisarhasan.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-ink-soft underline-offset-2 transition-colors hover:text-coral hover:underline"
          >
            Bisar Ul Hasan
          </a>
        </p>
      </div>
    </div>
  );
}

function EmptyState({ onCompose }: { onCompose: (lead: string) => void }) {
  return (
    <div className="animate-pop py-10 text-center">
      <p className="font-[family-name:var(--font-display)] text-2xl font-light text-ink">
        What shall we figure out today?
      </p>
      <p className="mx-auto mt-2 max-w-sm text-sm text-ink-soft">
        Name a topic and I&rsquo;ll take it from there — try one of these to get going:
      </p>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        {STARTERS.map((s, i) => (
          <button
            key={s.label}
            data-starter
            onClick={() => onCompose(s.lead)}
            className="animate-pop rounded-full border-2 border-ink/10 bg-white/60 px-4 py-2 text-sm font-semibold text-ink-soft transition-colors hover:border-sun hover:text-ink"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            {s.label} →
          </button>
        ))}
      </div>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex animate-pop justify-end">
      <div className="max-w-[80%] whitespace-pre-wrap rounded-[var(--radius-blob)] rounded-br-md bg-coral px-4 py-3 font-semibold text-white shadow-[0_3px_0_var(--color-coral-deep)]">
        {text}
      </div>
    </div>
  );
}

function PipBubble({ msg }: { msg: Msg }) {
  return (
    <div className="flex animate-pop items-start gap-3">
      <div className="mt-1 shrink-0">
        <Mascot size={72} />
      </div>
      <div className="max-w-[85%] space-y-3">
        <div
          className={`rounded-[var(--radius-blob)] rounded-tl-md border-2 px-4 py-3 leading-relaxed shadow-[0_3px_0_rgba(43,42,38,0.06)] ${
            msg.error
              ? "whitespace-pre-wrap border-coral/30 bg-coral/5 text-coral-deep"
              : "border-ink/8 bg-white text-ink"
          }`}
        >
          {msg.error ? (
            msg.text
          ) : (
            <div className="md">
              <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {normalizeMath(msg.text)}
              </Markdown>
            </div>
          )}
        </div>

        {msg.supported != null && !msg.error && (
          <ConfidenceBadge supported={msg.supported} confidence={msg.confidence} />
        )}

        {msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {msg.sources.map((s, i) => (
              <CitationChip key={i} source={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ConfidenceBadge({
  supported,
  confidence,
}: {
  supported: boolean;
  confidence?: string | null;
}) {
  if (!supported) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-sun/25 px-3 py-1 text-xs font-bold text-ink">
        🤔 Not fully covered in your book
      </span>
    );
  }
  const c = (confidence ?? "").toLowerCase();
  const tone =
    c === "high"
      ? "bg-teal/15 text-teal-deep"
      : c === "medium"
        ? "bg-sun/25 text-ink"
        : "bg-ink/8 text-ink-soft";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${tone}`}>
      ✓ Grounded in your textbook{c ? ` · ${c} confidence` : ""}
    </span>
  );
}

function CitationChip({ source }: { source: Source }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      onClick={() => setOpen((o) => !o)}
      className="group inline-flex max-w-full items-center gap-2 rounded-xl border-2 border-teal/25 bg-teal/8 px-3 py-1.5 text-left transition-colors hover:border-teal hover:bg-teal/12"
    >
      <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-teal/20 text-[10px]">
        📖
      </span>
      <span className="font-[family-name:var(--font-mono)] text-xs leading-tight text-teal-deep">
        {open ? source.label : `p.${source.page}${source.section ? ` · §${source.section}` : ""}`}
      </span>
    </button>
  );
}

function Typing() {
  return (
    <div className="flex animate-pop items-center gap-3">
      <Mascot size={36} />
      <div className="flex items-center gap-1.5 rounded-[var(--radius-blob)] rounded-tl-md border-2 border-ink/8 bg-white px-4 py-4 shadow-[0_3px_0_rgba(43,42,38,0.06)]">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="typing-dot h-2 w-2 rounded-full bg-teal"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
