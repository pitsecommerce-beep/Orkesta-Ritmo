"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, ArrowRight, CheckCircle } from "lucide-react";

const REGIMES_ALLOWED = [
  { value: "resico_pf", label: "RESICO Persona Física" },
  { value: "resico_pf_sueldos", label: "RESICO PF + Sueldos" },
  { value: "arrendamiento", label: "Arrendamiento" },
  { value: "arrendamiento_sueldos", label: "Arrendamiento + Sueldos" },
  { value: "resico_pm", label: "RESICO Persona Moral" },
];

const PERSON_TYPES = [
  { value: "pf", label: "Persona Física" },
  { value: "pm", label: "Persona Moral" },
];

type OnboardingData = {
  personType: string;
  rfc: string;
  regime: string;
  businessName: string;
  hasSueldos: string;
  ejercicio: string;
};

const TOTAL_STEPS = 6;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData>({
    personType: "",
    rfc: "",
    regime: "",
    businessName: "",
    hasSueldos: "",
    ejercicio: "2025",
  });
  const [rejected, setRejected] = useState(false);

  function update(field: keyof OnboardingData, value: string) {
    setData((prev) => ({ ...prev, [field]: value }));
  }

  function next() {
    if (step === 3) {
      const allowed = REGIMES_ALLOWED.map((r) => r.value);
      if (!allowed.includes(data.regime)) {
        setRejected(true);
        return;
      }
    }
    setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  }

  function back() {
    setRejected(false);
    setStep((s) => Math.max(s - 1, 1));
  }

  function finish() {
    router.push("/dashboard");
  }

  if (rejected) {
    return (
      <OnboardingShell step={step}>
        <div className="text-center">
          <h2 className="font-heading text-xl font-bold">Régimen no soportado</h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Por el momento, Ritmo no soporta tu régimen fiscal. Regístrate en la lista de espera y
            te avisamos cuando esté disponible.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Link href="/lista-espera">
              <Button className="w-full">Ir a lista de espera</Button>
            </Link>
            <Button variant="outline" onClick={back}>Volver</Button>
          </div>
        </div>
      </OnboardingShell>
    );
  }

  return (
    <OnboardingShell step={step}>
      {step === 1 && (
        <StepCard
          title="¿Eres persona física o moral?"
          onNext={next}
          canNext={!!data.personType}
        >
          <div className="space-y-3">
            {PERSON_TYPES.map((pt) => (
              <button
                key={pt.value}
                type="button"
                onClick={() => update("personType", pt.value)}
                className={`w-full rounded-lg border p-4 text-left transition-colors ${
                  data.personType === pt.value
                    ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5"
                    : "hover:border-muted-foreground/30"
                }`}
              >
                <span className="font-heading font-semibold">{pt.label}</span>
              </button>
            ))}
          </div>
        </StepCard>
      )}

      {step === 2 && (
        <StepCard
          title="¿Cuál es tu RFC?"
          onNext={next}
          onBack={back}
          canNext={data.rfc.length >= 12}
        >
          <div>
            <Label htmlFor="rfc">RFC</Label>
            <Input
              id="rfc"
              value={data.rfc}
              onChange={(e) => update("rfc", e.target.value.toUpperCase())}
              placeholder={data.personType === "pm" ? "XXX010101AAA" : "XXXX010101AAA"}
              maxLength={13}
              className="mt-1 font-mono uppercase"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              {data.personType === "pf" ? "13 caracteres" : "12 caracteres"} con homoclave
            </p>
          </div>
        </StepCard>
      )}

      {step === 3 && (
        <StepCard
          title="¿Cuál es tu régimen fiscal?"
          onNext={next}
          onBack={back}
          canNext={!!data.regime}
        >
          <Select value={data.regime} onValueChange={(v) => update("regime", v)}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona tu régimen" />
            </SelectTrigger>
            <SelectContent>
              {REGIMES_ALLOWED.map((r) => (
                <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
              ))}
              <SelectItem value="otro">Otro régimen</SelectItem>
            </SelectContent>
          </Select>
        </StepCard>
      )}

      {step === 4 && (
        <StepCard
          title="Nombre o razón social"
          onNext={next}
          onBack={back}
          canNext={data.businessName.length >= 2}
        >
          <div>
            <Label htmlFor="name">
              {data.personType === "pm" ? "Razón social" : "Nombre completo"}
            </Label>
            <Input
              id="name"
              value={data.businessName}
              onChange={(e) => update("businessName", e.target.value)}
              placeholder={data.personType === "pm" ? "Mi Empresa S.A. de C.V." : "Juan Pérez López"}
              className="mt-1"
            />
          </div>
        </StepCard>
      )}

      {step === 5 && (
        <StepCard
          title="¿También recibes sueldos y salarios?"
          onNext={next}
          onBack={back}
          canNext={!!data.hasSueldos}
        >
          <div className="space-y-3">
            {[
              { value: "si", label: "Sí, también recibo nómina" },
              { value: "no", label: "No, solo tengo el régimen seleccionado" },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => update("hasSueldos", opt.value)}
                className={`w-full rounded-lg border p-4 text-left transition-colors ${
                  data.hasSueldos === opt.value
                    ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5"
                    : "hover:border-muted-foreground/30"
                }`}
              >
                <span className="text-sm font-medium">{opt.label}</span>
              </button>
            ))}
          </div>
        </StepCard>
      )}

      {step === 6 && (
        <StepCard
          title="¡Listo para empezar!"
          onBack={back}
          canNext
          nextLabel="Ir al dashboard"
          onNext={finish}
        >
          <div className="space-y-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>RFC: <strong className="text-foreground font-mono">{data.rfc}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>Régimen: <strong className="text-foreground">{REGIMES_ALLOWED.find((r) => r.value === data.regime)?.label}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>{data.businessName}</span>
            </div>
            <p className="mt-4 text-xs">
              Podrás modificar estos datos más adelante en la configuración del workspace.
            </p>
          </div>
        </StepCard>
      )}
    </OnboardingShell>
  );
}

function OnboardingShell({ step, children }: { step: number; children: React.ReactNode }) {
  return (
    <div className="flex min-h-full flex-col items-center px-4 py-12">
      <Logo type="full" className="mb-8 animate-fade-in" />
      <div className="mb-6 w-full max-w-md">
        <Progress value={(step / TOTAL_STEPS) * 100} className="h-2" />
        <p className="mt-1 text-right text-xs text-muted-foreground">Paso {step} de {TOTAL_STEPS}</p>
      </div>
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}

function StepCard({
  title,
  children,
  onNext,
  onBack,
  canNext,
  nextLabel = "Continuar",
}: {
  title: string;
  children: React.ReactNode;
  onNext?: () => void;
  onBack?: () => void;
  canNext: boolean;
  nextLabel?: string;
}) {
  return (
    <Card className="animate-scale-in">
      <CardHeader>
        <CardTitle className="font-heading text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {children}
        <div className="flex gap-3">
          {onBack && (
            <Button variant="outline" onClick={onBack} className="gap-1">
              <ArrowLeft className="h-4 w-4" /> Atrás
            </Button>
          )}
          {onNext && (
            <Button onClick={onNext} disabled={!canNext} className="ml-auto gap-1">
              {nextLabel} <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
