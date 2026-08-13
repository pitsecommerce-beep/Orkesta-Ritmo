"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, Shield, Mail, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase";
import { Button } from "@/components/ui/button";

export function TarifaAlertBanner({ ejercicio = 2026 }: { ejercicio?: number }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--color-warning)]/20 bg-[var(--color-warning-light)] p-4 text-sm">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-warning)]" />
      <div>
        <p className="font-medium text-amber-900 dark:text-amber-200">
          Tarifas {ejercicio} no disponibles
        </p>
        <p className="mt-1 text-amber-800/80 dark:text-amber-300/80">
          El SAT aún no ha publicado las tarifas fiscales para el ejercicio {ejercicio}.
          Los períodos de {ejercicio} no se pueden calcular hasta que las tarifas se capturen en el sistema.
        </p>
      </div>
    </div>
  );
}

export function EmailVerificationBanner() {
  const [show, setShow] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    async function check() {
      const supabase = createClient();
      if (!supabase) return;

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data: profile } = await supabase
        .from("user_profiles")
        .select("email_verificado")
        .eq("id", user.id)
        .maybeSingle();

      if (!profile || !profile.email_verificado) {
        setShow(true);
      }
    }
    check();
  }, []);

  if (!show) return null;

  async function handleVerify() {
    setSending(true);
    const supabase = createClient();
    if (!supabase) return;

    const { data: { user } } = await supabase.auth.getUser();
    if (!user?.email) return;

    await supabase.auth.signInWithOtp({
      email: user.email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback?verify=true`,
      },
    });

    setSending(false);
    setSent(true);
  }

  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--color-warning)]/20 bg-[var(--color-warning-light)] p-4 text-sm">
      <Mail className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-warning)]" />
      <div className="flex-1">
        <p className="font-medium text-amber-900 dark:text-amber-200">
          Verifica tu correo electronico
        </p>
        <p className="mt-1 text-amber-800/80 dark:text-amber-300/80">
          Para calcular y presentar tus declaraciones necesitas verificar tu correo.
        </p>
        {sent ? (
          <p className="mt-2 text-sm font-medium text-green-700 dark:text-green-400">
            Revisa tu bandeja de entrada y haz clic en el enlace de verificacion.
          </p>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={handleVerify}
            disabled={sending}
          >
            {sending ? (
              <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> Enviando...</>
            ) : (
              "Enviar correo de verificacion"
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

export function PrivacyReviewBanner() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--color-azul)]/20 bg-[var(--color-primary-light)] p-4 text-sm">
      <Shield className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-azul)]" />
      <div>
        <p className="font-medium text-blue-900 dark:text-blue-200">
          Aviso de privacidad en revisión
        </p>
        <p className="mt-1 text-blue-800/80 dark:text-blue-300/80">
          El aviso de privacidad y los términos de servicio se encuentran en revisión legal
          para su conformidad con la LFPDPPP. El documento definitivo será publicado antes
          del lanzamiento público.
        </p>
      </div>
    </div>
  );
}
