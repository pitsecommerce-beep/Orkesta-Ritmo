"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookie_consent");
    if (!consent) setVisible(true);
  }, []);

  function accept(analytics: boolean) {
    localStorage.setItem(
      "cookie_consent",
      JSON.stringify({ essential: true, analytics, ts: new Date().toISOString() }),
    );
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 border-t bg-background p-4 shadow-lg">
      <div className="mx-auto flex max-w-4xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          Usamos cookies esenciales para el funcionamiento del sitio. Las cookies de analítica están
          desactivadas por defecto.{" "}
          <a href="/privacidad" className="underline">
            Aviso de privacidad
          </a>
          .
        </p>
        <div className="flex gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={() => accept(false)}>
            Solo esenciales
          </Button>
          <Button size="sm" onClick={() => accept(true)}>
            Aceptar todas
          </Button>
        </div>
      </div>
    </div>
  );
}
