"use client";

import { useEffect } from "react";

export function EnvChecker() {
  useEffect(() => {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (supabaseUrl && supabaseKey) {
      console.info("%c[Orkesta Ritmo] Supabase conectado.", "color: #4caf50");
    }
  }, []);

  return null;
}
