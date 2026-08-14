"use client";

import { useState, useEffect, useCallback, useRef } from "react";
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
    body: "Tu herramienta para preparar y calcular tus declaraciónes fiscales RESICO de forma sencilla. Te explicamos como funciona en 5 pasos rápidos.",
    target: null,
  },
  {
    icon: Upload,
    title: "1. Sube tus documentos",
    body: "En la sección de Documentos sube tus CFDIs (archivos XML) y estados de cuenta bancarios. El sistema los procesa y clasifica automáticamente.",
    target: "/dashboard/documentos",
  },
  {
    icon: Calendar,
    title: "2. Revisa tus periodos",
    body: "En Periodos verás tus obligaciones fiscales mensuales organizadas por ISR e IVA. Cada periodo muestra su estado y fecha limite.",
    target: "/dashboard/periodos",
  },
  {
    icon: Calculator,
    title: "3. Calcula tu declaración",
    body: "Cuando tus documentos estén procesados, ejecuta el calculo fiscal. El motor de Ritmo aplica las tarifas RESICO vigentes y genera el desglose completo.",
    target: "/dashboard/periodos",
  },
  {
    icon: FileText,
    title: "4. CFDIs y extractos",
    body: "Consulta todos tus comprobantes fiscales en CFDIs y concilia tus movimientos bancarios en Extractos para asegurar que todo cuadra.",
    target: "/dashboard/cfdis",
  },
  {
    icon: MessageSquare,
    title: "5. Asistente fiscal",
    body: "Si tienes dudas, el Asistente esta disponible en el panel lateral para responder preguntas sobre tu situación fiscal.",
    target: "/dashboard/chat",
  },
];

const DESKTOP_BREAKPOINT = 768;

export function OnboardingTour({ onComplete: onCompleteCb }: { onComplete?: () => void } = {}) {
  const [show, setShow] = useState(true);
  const [step, setStep] = useState(0);
  const [isDesktop, setIsDesktop] = useState(false);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number } | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleResize() {
      setIsDesktop(window.innerWidth >= DESKTOP_BREAKPOINT);
    }
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const positionPopover = useCallback(() => {
    const current = STEPS[step];
    if (!isDesktop || !current.target) {
      setPopoverPos(null);
      return;
    }

    const targetEl = document.querySelector(
      `[data-tour-target="${current.target}"]`
    ) as HTMLElement | null;

    if (!targetEl) {
      setPopoverPos(null);
      return;
    }

    const rect = targetEl.getBoundingClientRect();
    const popoverEl = popoverRef.current;
    const popoverHeight = popoverEl ? popoverEl.offsetHeight : 260;

    let top = rect.top + rect.height / 2 - popoverHeight / 2;
    const minTop = 16;
    const maxTop = window.innerHeight - popoverHeight - 16;
    top = Math.max(minTop, Math.min(maxTop, top));

    setPopoverPos({
      top,
      left: rect.right + 16,
    });
  }, [step, isDesktop]);

  useEffect(() => {
    if (!show) return;
    positionPopover();
    window.addEventListener("resize", positionPopover);
    return () => window.removeEventListener("resize", positionPopover);
  }, [show, positionPopover]);

  useEffect(() => {
    if (!show || !isDesktop) return;
    const current = STEPS[step];
    if (!current.target) return;

    const targetEl = document.querySelector(
      `[data-tour-target="${current.target}"]`
    ) as HTMLElement | null;
    if (!targetEl) return;

    targetEl.classList.add("tour-highlight");
    return () => {
      targetEl.classList.remove("tour-highlight");
    };
  }, [show, step, isDesktop]);

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
    onCompleteCb?.();
  }

  if (!show) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const Icon = current.icon;
  const usePositioned = isDesktop && current.target && popoverPos;

  return (
    <>
      <style>{`
        .tour-highlight {
          position: relative;
          z-index: 51;
          background: var(--color-primary-light) !important;
          box-shadow: 0 0 0 3px var(--color-azul), 0 0 16px rgba(59, 130, 246, 0.3);
          border-radius: 0.375rem;
          animation: tour-pulse 2s ease-in-out infinite;
        }
        @keyframes tour-pulse {
          0%, 100% { box-shadow: 0 0 0 3px var(--color-azul), 0 0 16px rgba(59, 130, 246, 0.3); }
          50% { box-shadow: 0 0 0 5px var(--color-azul), 0 0 24px rgba(59, 130, 246, 0.5); }
        }
        .tour-arrow {
          position: absolute;
          left: -8px;
          top: 50%;
          transform: translateY(-50%);
          width: 0;
          height: 0;
          border-top: 10px solid transparent;
          border-bottom: 10px solid transparent;
          border-right: 10px solid var(--color-border, hsl(var(--border)));
        }
        .tour-arrow-inner {
          position: absolute;
          left: -6px;
          top: 50%;
          transform: translateY(-50%);
          width: 0;
          height: 0;
          border-top: 9px solid transparent;
          border-bottom: 9px solid transparent;
          border-right: 9px solid hsl(var(--background));
        }
      `}</style>

      <div className="fixed inset-0 z-50">
        <div
          className="absolute inset-0 bg-black/60 animate-fade-in"
          onClick={complete}
        />

        <div
          ref={popoverRef}
          className={
            usePositioned
              ? "fixed z-[52] w-full max-w-sm rounded-lg border bg-background p-6 shadow-lg animate-scale-in"
              : "absolute inset-0 z-10 flex items-center justify-center"
          }
          style={
            usePositioned
              ? { top: popoverPos.top, left: popoverPos.left }
              : undefined
          }
        >
          {usePositioned ? (
            <PopoverContent
              icon={Icon}
              title={current.title}
              body={current.body}
              step={step}
              totalSteps={STEPS.length}
              isLast={isLast}
              onComplete={complete}
              onPrev={() => setStep((s) => s - 1)}
              onNext={() => setStep((s) => s + 1)}
              showArrow
            />
          ) : (
            <div className="relative z-10 w-full max-w-md mx-4 rounded-lg border bg-background p-6 shadow-lg animate-scale-in">
              <PopoverContent
                icon={Icon}
                title={current.title}
                body={current.body}
                step={step}
                totalSteps={STEPS.length}
                isLast={isLast}
                onComplete={complete}
                onPrev={() => setStep((s) => s - 1)}
                onNext={() => setStep((s) => s + 1)}
                showArrow={false}
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function PopoverContent({
  icon: Icon,
  title,
  body,
  step,
  totalSteps,
  isLast,
  onComplete,
  onPrev,
  onNext,
  showArrow,
}: {
  icon: React.ElementType;
  title: string;
  body: string;
  step: number;
  totalSteps: number;
  isLast: boolean;
  onComplete: () => void;
  onPrev: () => void;
  onNext: () => void;
  showArrow: boolean;
}) {
  return (
    <>
      {showArrow && (
        <>
          <div className="tour-arrow" />
          <div className="tour-arrow-inner" />
        </>
      )}

      <button
        onClick={onComplete}
        className="absolute right-3 top-3 rounded-sm p-1 text-muted-foreground hover:text-foreground transition-opacity"
        aria-label="Cerrar"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex flex-col items-center text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-primary-light)]">
          <Icon className="h-6 w-6 text-[var(--color-azul)]" />
        </div>

        <h2 className="mt-4 font-heading text-lg font-bold">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
          {body}
        </p>
      </div>

      <div className="mt-6">
        <Progress value={((step + 1) / totalSteps) * 100} className="h-1.5" />
        <p className="mt-1 text-right text-xs text-muted-foreground">
          {step + 1} de {totalSteps}
        </p>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={onComplete}
          className="text-muted-foreground"
        >
          Omitir
        </Button>

        <div className="flex gap-2">
          {step > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onPrev}
              className="gap-1"
            >
              <ArrowLeft className="h-3.5 w-3.5" /> Atrás
            </Button>
          )}
          {isLast ? (
            <Button size="sm" onClick={onComplete} className="gap-1">
              Comenzar <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button size="sm" onClick={onNext} className="gap-1">
              Siguiente <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </>
  );
}
