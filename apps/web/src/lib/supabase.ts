import { createBrowserClient } from "@supabase/ssr";
import { isSupabaseConfigured } from "./env";

let warned = false;

export function createClient() {
  if (!isSupabaseConfigured()) {
    if (!warned && typeof window !== "undefined") {
      console.warn(
        "[Orkesta Ritmo] Supabase no configurado. Define NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY en .env.local",
      );
      warned = true;
    }
    return null;
  }

  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
