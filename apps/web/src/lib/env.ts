const REQUIRED_ENV = [
  { key: "NEXT_PUBLIC_SUPABASE_URL", label: "Supabase URL" },
  { key: "NEXT_PUBLIC_SUPABASE_ANON_KEY", label: "Supabase Anon Key" },
] as const;

const OPTIONAL_ENV = [
  { key: "NEXT_PUBLIC_API_URL", label: "API URL", fallback: "http://localhost:8000/api" },
] as const;

export type EnvStatus = {
  missing: { key: string; label: string }[];
  configured: { key: string; label: string }[];
  optional: { key: string; label: string; fallback: string }[];
};

export function checkEnv(): EnvStatus {
  const missing: EnvStatus["missing"] = [];
  const configured: EnvStatus["configured"] = [];

  for (const v of REQUIRED_ENV) {
    const val = process.env[v.key];
    if (!val) {
      missing.push(v);
    } else {
      configured.push(v);
    }
  }

  const optional: EnvStatus["optional"] = [];
  for (const v of OPTIONAL_ENV) {
    if (!process.env[v.key]) {
      optional.push(v);
    }
  }

  return { missing, configured, optional };
}

export function isSupabaseConfigured(): boolean {
  return !!(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
}
