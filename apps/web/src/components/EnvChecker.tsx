"use client";

import { useEffect } from "react";

const ENV_VARS = [
  { key: "NEXT_PUBLIC_SUPABASE_URL", required: true },
  { key: "NEXT_PUBLIC_SUPABASE_ANON_KEY", required: true },
  { key: "NEXT_PUBLIC_API_URL", required: false, fallback: "http://localhost:8000/api" },
];

export function EnvChecker() {
  useEffect(() => {
    const missing: string[] = [];
    const optional: string[] = [];

    for (const v of ENV_VARS) {
      const val = process.env[v.key];
      if (!val) {
        if (v.required) {
          missing.push(v.key);
        } else {
          optional.push(`${v.key} (usando fallback: ${v.fallback})`);
        }
      }
    }

    if (missing.length > 0) {
      console.warn(
        `%c[Orkesta Ritmo] Variables de entorno faltantes:%c\n\n` +
          missing.map((k) => `  • ${k}`).join("\n") +
          "\n\n" +
          "Crea un archivo .env.local en apps/web/ con estas variables.\n" +
          "La app funciona en modo demo sin ellas, pero la autenticación y datos reales no estarán disponibles.\n" +
          "Consulta .env.example en la raíz del proyecto para ver todas las variables disponibles.",
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
