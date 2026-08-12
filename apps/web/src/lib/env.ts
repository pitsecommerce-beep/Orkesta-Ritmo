export type EnvStatus = {
  missing: { key: string; label: string }[];
  configured: { key: string; label: string }[];
  optional: { key: string; label: string; fallback: string }[];
};

export function checkEnv(): EnvStatus {
  const missing: EnvStatus["missing"] = [];
  const configured: EnvStatus["configured"] = [];
  const optional: EnvStatus["optional"] = [];

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (supabaseUrl) {
    configured.push({ key: "NEXT_PUBLIC_SUPABASE_URL", label: "Supabase URL" });
  } else {
    missing.push({ key: "NEXT_PUBLIC_SUPABASE_URL", label: "Supabase URL" });
  }

  if (supabaseKey) {
    configured.push({ key: "NEXT_PUBLIC_SUPABASE_ANON_KEY", label: "Supabase Anon Key" });
  } else {
    missing.push({ key: "NEXT_PUBLIC_SUPABASE_ANON_KEY", label: "Supabase Anon Key" });
  }

  if (!apiUrl) {
    optional.push({ key: "NEXT_PUBLIC_API_URL", label: "API URL", fallback: "http://localhost:8000/api" });
  }

  return { missing, configured, optional };
}

export function isSupabaseConfigured(): boolean {
  return !!(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
}
