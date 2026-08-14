"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { createClient } from "@/lib/supabase";
import {
  Upload,
  Calendar,
  Calculator,
  FileText,
  MessageSquare,
  ArrowRight,
  ArrowLeft,
  X,
  Sparkles,
} from "lucide-react";

const STEPS = [
  {
    icon: Sparkles,
    title: "Bienvenido a Ritmo",
    body: "Tu herramienta para preparar y calcular tus declaraciones fiscales RESICO de forma sencilla. Te explicamos como funciona en 5 pasos rapidos.",
  },
  {
    icon: Upload,
    title: "1. Sube tus documentos",
    body: "En la seccion de Documentos sube tus CFDIs (archivos XML) y estados de cuenta bancarios. El sistema los procesa y clasifica automaticamente.",
  },
  {
    icon: Calendar,
    title: "2. Revisa tus periodos",
    body: "En Periodos veras tus obligaciones fiscales mensuales organizadas por ISR e IVA. Cada periodo muestra su estado y fecha limite.",
  },
  {
    icon: Calculator,
    title: "3. Calcula tu declaracion",
    body: "Cuando tus documentos esten procesados, ejecuta el calculo fiscal. El motor de Ritmo aplica las tarifas RESICO vigentes y genera el desglose completo.",
  },
  {
    icon: FileText,
    title: "4. CFDIs y extractos",
    body: "Consulta todos tus comprobantes fiscales en CFDIs y concilia tus movimientos bancarios en Extractos para asegurar que todo cuadra.",
  },
  {
    icon: MessageSquare,
    title: "5. Asistente fiscal",
    body: "Si tienes dudas, el Asistente esta disponible en el panel lateral para responder preguntas sobre tu situacion fiscal.",
  },
];

export function OnboardingTour() {
  const [show, setShow] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    async function check() {
      const supabase = createClient();
      if (!supabase) return;

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data: profile } = await supabase
        .from("user_profiles")
        .select("onboarding_completado")
        .eq("id", user.id)
        .maybeSingle();

      if (profile && !profile.onboarding_completado) {
        setShow(true);
      }
    }
    check();
  }, []);

  async function complete() {
    const supabase = createClient();
    if (!supabase) return;

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    await supabase
      .from("user_profiles")
      .update({ onboarding_completado: true })
      .eq("id", user.id);

    setShow(false);
  }

  if (!show) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const Icon = current.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 animate-fade-in" onClick={complete} />

      <div className="relative z-10 w-full max-w-md mx-4 rounded-lg border bg-background p-6 shadow-lg animate-scale-in">
        <button
          onClick={complete}
          className="absolute right-3 top-3 rounded-sm p-1 text-muted-foreground hover:text-foreground transition-opacity"
          aria-label="Cerrar"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-primary-light)]">
            <Icon className="h-6 w-6 text-[var(--color-azul)]" />
          </div>

          <h2 className="mt-4 font-heading text-lg font-bold">{current.title}</h2>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            {current.body}
          </p>
        </div>

        <div className="mt-6">
          <Progress value={((step + 1) / STEPS.length) * 100} className="h-1.5" />
          <p className="mt-1 text-right text-xs text-muted-foreground">
            {step + 1} de {STEPS.length}
          </p>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={complete}
            className="text-muted-foreground"
          >
            Omitir
          </Button>

          <div className="flex gap-2">
            {step > 0 && (
              <Button variant="outline" size="sm" onClick={() => setStep(s => s - 1)} className="gap-1">
                <ArrowLeft className="h-3.5 w-3.5" /> Atras
              </Button>
            )}
            {isLast ? (
              <Button size="sm" onClick={complete} className="gap-1">
                Comenzar <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button size="sm" onClick={() => setStep(s => s + 1)} className="gap-1">
                Siguiente <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
