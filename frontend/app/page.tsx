"use client";

import { useEffect, useState } from "react";
import { fetchCatalog, type ClassOption } from "@/lib/api";
import ClassPicker from "@/components/ClassPicker";
import Chat from "@/components/Chat";
import Mascot from "@/components/Mascot";

const STORE_KEY = "pip.class";

export default function Home() {
  const [catalog, setCatalog] = useState<ClassOption[] | null>(null);
  const [error, setError] = useState(false);
  const [cls, setCls] = useState<ClassOption | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORE_KEY);
      if (saved) setCls(JSON.parse(saved));
    } catch {}
    setReady(true);
    fetchCatalog().then(setCatalog).catch(() => setError(true));
  }, []);

  function pick(c: ClassOption) {
    setCls(c);
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(c));
    } catch {}
  }

  function switchClass() {
    setCls(null);
    try {
      localStorage.removeItem(STORE_KEY);
    } catch {}
  }

  if (!ready) return null;

  if (cls) return <Chat cls={cls} onSwitchClass={switchClass} />;

  if (error)
    return (
      <Centered>
        <Mascot size={96} />
        <p className="mt-5 font-[family-name:var(--font-display)] text-2xl text-ink">
          I can&rsquo;t reach the assistant
        </p>
        <p className="mt-2 max-w-sm text-ink-soft">
          The backend isn&rsquo;t responding. Make sure it&rsquo;s running, then refresh.
        </p>
      </Centered>
    );

  if (!catalog)
    return (
      <Centered>
        <Mascot size={96} bob />
        <p className="mt-5 text-ink-soft">Getting your books ready…</p>
      </Centered>
    );

  return <ClassPicker catalog={catalog} onPick={pick} />;
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative z-10 flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      {children}
    </div>
  );
}
