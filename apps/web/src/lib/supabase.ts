import { createBrowserClient } from "@supabase/ssr";
import { isSupabaseConfigured } from "./env";

let warned = false;

export function createClient() {
  if (!isSupabaseConfigured()) {
    warned = true;
    return null;
  }

  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
