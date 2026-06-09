"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import Mascot from "./Mascot";

export default function Auth() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        // If email confirmation is on, no session is returned yet.
        if (!data.session) {
          setNotice("Account created! Check your email to confirm, then sign in.");
          setMode("signin");
        }
        // If a session is returned, the auth listener logs them straight in.
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <div className="relative z-10 flex min-h-dvh flex-col items-center justify-center px-6 py-16">
      <div className="animate-rise" style={{ animationDelay: "40ms" }}>
        <Mascot size={104} bob />
      </div>
      <h1
        className="mt-5 font-[family-name:var(--font-display)] text-4xl font-light tracking-tight text-ink animate-rise sm:text-5xl"
        style={{ animationDelay: "120ms" }}
      >
        {isSignup ? "Create your account" : "Welcome to Noor"}
      </h1>
      <p className="mt-2 text-ink-soft animate-rise" style={{ animationDelay: "200ms" }}>
        {isSignup
          ? "Sign up to start asking your textbooks."
          : "Sign in to ask your textbooks."}
      </p>

      <form
        onSubmit={submit}
        className="mt-8 w-full max-w-sm animate-rise space-y-3"
        style={{ animationDelay: "280ms" }}
      >
        <input
          type="email"
          required
          autoComplete="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-[var(--radius-blob)] border-2 border-ink/10 bg-white/80 px-4 py-3 text-ink outline-none transition-colors placeholder:text-ink-soft/60 focus:border-teal"
        />
        <input
          type="password"
          required
          minLength={6}
          autoComplete={isSignup ? "new-password" : "current-password"}
          placeholder="Password (min 6 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-[var(--radius-blob)] border-2 border-ink/10 bg-white/80 px-4 py-3 text-ink outline-none transition-colors placeholder:text-ink-soft/60 focus:border-teal"
        />

        {error && (
          <p className="rounded-xl bg-coral/10 px-3 py-2 text-sm font-semibold text-coral-deep">
            {error}
          </p>
        )}
        {notice && (
          <p className="rounded-xl bg-sun/25 px-3 py-2 text-sm font-semibold text-ink">
            {notice}
          </p>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-[var(--radius-blob)] bg-teal py-3 text-lg font-bold text-white shadow-[0_4px_0_var(--color-teal-deep)] transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_0_var(--color-teal-deep)] active:translate-y-0.5 active:shadow-none disabled:cursor-not-allowed disabled:opacity-60"
        >
          {busy ? "…" : isSignup ? "Create account" : "Sign in"}
        </button>
      </form>

      <button
        onClick={() => {
          setMode(isSignup ? "signin" : "signup");
          setError(null);
          setNotice(null);
        }}
        className="mt-5 text-sm text-ink-soft transition-colors hover:text-teal-deep"
      >
        {isSignup ? "Already have an account? Sign in" : "New here? Create an account"}
      </button>

      <p className="mt-10 text-center text-xs text-ink-soft/60">
        Made with <span className="text-coral">♥</span> by{" "}
        <a
          href="https://bisarhasan.com"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold underline-offset-2 hover:text-coral hover:underline"
        >
          Bisar Ul Hasan
        </a>
      </p>
    </div>
  );
}
