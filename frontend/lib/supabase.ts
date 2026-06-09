import { createClient } from "@supabase/supabase-js";

// Public client keys (anon/publishable) — safe to ship in the browser; row-level
// security protects data server-side. Set in Vercel + .env.local.
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
);
