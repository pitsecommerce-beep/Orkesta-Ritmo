"use client";

import { useEffect } from "react";

const ENV_SNAPSHOT = {
  NEXT_PUBLIC_SUPABASE_URL: {
    value: process.env.NEXT_PUBLIC_SUPABASE_URL,
    required: true,
  },
  NEXT_PUBLIC_SUPABASE_ANON_KEY: {
    value: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    required: true,
  },
  NEXT_PUBLIC_API_URL: {
    value: process.env.NEXT_PUBLIC_API_URL,
    required: false,
    fallback: "http://localhost:8000/api",
  },
};

export function EnvChecker() {
  useEffect(() => {
    const missing: string[] = [];
    const optional: string[] = [];

    for (const [key, v] of Object.entries(ENV_SNAPSHOT)) {
      if (!v.value) {
        if (v.required) {
          missing.push(key);
        } else {
          optional.push(`${key} (usando fallback: ${"fallback" in v ? v.fallback : "—"})`);
        }
      }
    }

    if (missing.length > 0) {
      console.warn(
        `%c[Orkesta Ritmo] Variables de entorno faltantes:%c\n\n` +
          missing.map((k) => `  • ${k}`).join("\n") +
          "\n\n" +
          "Configura estas variables en tu entorno de despliegue (Railway, Vercel, etc.)\n" +
          "o crea un archivo .env.local en apps/web/ para desarrollo local.\n" +
          "La app funciona en modo demo sin ellas, pero la autenticación y datos reales no estarán disponibles.",
        "color: #ff9800; font-weight: bold; font-size: 14px",
        "color: #ff9800",
      );
    }

    if (optional.length > 0) {
      console.info(
        `%c[Orkesta Ritmo] Variables opcionales no configuradas:%c\n` +
          optional.map((k) => `  • ${k}`).join("\n"),
        "color: #2196f3; font-weight: bold",
        "color: #2196f3",
      );
    }

    if (missing.length === 0 && optional.length === 0) {
      console.info("%c[Orkesta Ritmo] Todas las variables de entorno están configuradas.", "color: #4caf50");
    }
  }, []);

  return null;
}
