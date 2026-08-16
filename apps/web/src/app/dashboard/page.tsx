"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Calendar,
  FileText,
  Clock,
  FolderOpen,
  Loader2,
} from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";

const REGIMEN_LABELS: Record<string, string> = {
  RESICO_PF: "RESICO Persona Física",
  RESICO_PF_SUELDOS: "RESICO PF + Sueldos",
  ARRENDAMIENTO: "Arrendamiento",
  ARRENDAMIENTO_SUELDOS: "Arrendamiento + Sueldos",
};

const ESTADO_LABELS: Record<string, string> = {
  borrador: "Borrador",
  calculado: "Calculado",
  contrastado: "Contrastado",
  preparado: "Preparado",
  presentado: "Presentado",
  cerrado: "Cerrado",
  con_diferencia: "Con diferencia",
  requiere_revision: "Requiere revisión",
  omitido: "Omitido",
};

const ESTADO_COLORS: Record<string, string> = {
  borrador: "bg-gray-100 text-gray-700",
  calculado: "bg-blue-100 text-blue-700",
  contrastado: "bg-indigo-100 text-indigo-700",
  preparado: "bg-purple-100 text-purple-700",
  presentado: "bg-green-100 text-green-700",
  cerrado: "bg-green-200 text-green-800",
  con_diferencia: "bg-yellow-100 text-yellow-700",
  requiere_revision: "bg-red-100 text-red-700",
  omitido: "bg-gray-200 text-gray-500",
};

const MES_LABELS = [
  "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

interface PeriodoRow {
  id: string;
  impuesto: string;
  tipo_periodo: string;
  ejercicio: number;
  numero_periodo: number;
  fecha_limite: string;
  estado: string;
  resultado_json: Record<string, unknown> | null;
}

const MOCK_PERIODOS: PeriodoRow[] = [
  { id: "m1", impuesto: "ISR", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 1, fecha_limite: "2025-02-17", estado: "presentado", resultado_json: { isr_a_cargo: 1250 } },
  { id: "m2", impuesto: "IVA", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 1, fecha_limite: "2025-02-17", estado: "presentado", resultado_json: { iva_determinado: 1856 } },
  { id: "m3", impuesto: "ISR", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 2, fecha_limite: "2025-03-17", estado: "presentado", resultado_json: { isr_a_cargo: 2100 } },
  { id: "m4", impuesto: "IVA", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 2, fecha_limite: "2025-03-17", estado: "presentado", resultado_json: { iva_determinado: 2320 } },
  { id: "m5", impuesto: "ISR", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 3, fecha_limite: "2025-04-17", estado: "calculado", resultado_json: { isr_a_cargo: 1800 } },
  { id: "m6", impuesto: "IVA", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 3, fecha_limite: "2025-04-17", estado: "borrador", resultado_json: null },
];

export default function DashboardHome() {
  const { demoMode } = useDemoMode();
  const { tenant, loading: tenantLoading } = useTenant();
  const [periodos, setPeriodos] = useState<PeriodoRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (demoMode) {
      setPeriodos(MOCK_PERIODOS);
      setLoading(false);
      return;
    }

    setPeriodos([]);
    setLoading(true);

    if (tenantLoading) return;

    async function load() {
      if (!tenant) { setLoading(false); return; }

      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data } = await supabase
        .from("periodos")
        .select("id, impuesto, tipo_periodo, ejercicio, numero_periodo, fecha_limite, estado, resultado_json")
        .eq("tenant_id", tenant.tenantId)
        .order("ejercicio", { ascending: false })
        .order("numero_periodo", { ascending: true });

      setPeriodos((data ?? []) as PeriodoRow[]);
      setLoading(false);
    }
    load();
  }, [demoMode, tenant, tenantLoading]);

  const pendientes = periodos.filter(p => !["presentado", "cerrado"].includes(p.estado));
  const presentados = periodos.filter(p => ["presentado", "cerrado"].includes(p.estado));

  const isrTotal = periodos
    .filter(p => p.impuesto === "ISR" && p.resultado_json)
    .reduce((sum, p) => sum + (Number((p.resultado_json as Record<string, unknown>)?.isr_a_cargo) || 0), 0);

  const ivaTotal = periodos
    .filter(p => p.impuesto === "IVA" && p.resultado_json)
    .reduce((sum, p) => sum + (Number((p.resultado_json as Record<string, unknown>)?.iva_determinado) || 0), 0);

  const totalObligaciones = periodos.length;
  const progreso = totalObligaciones > 0 ? Math.round((presentados.length / totalObligaciones) * 100) : 0;

  const regimenLabel = demoMode
    ? "RESICO Persona Física"
    : tenant ? (REGIMEN_LABELS[tenant.regimen] ?? tenant.regimen) : "";

  const ejercicio = periodos.length > 0 ? periodos[0].ejercicio : new Date().getFullYear();

  if (loading || tenantLoading) {
    return (
      <div className="flex items-center justify-center p-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up mb-8">
        <h1 className="font-heading text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Ejercicio {ejercicio}{regimenLabel ? ` — ${regimenLabel}` : ""}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="animate-fade-in-up stagger-1 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Periodos pendientes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{pendientes.length}</p>
            <p className="text-xs text-muted-foreground">de {totalObligaciones} obligaciones</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-2 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">ISR acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{formatMXN(isrTotal)}</p>
            <p className="text-xs text-muted-foreground">ISR a cargo acumulado</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-3 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">IVA acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{formatMXN(ivaTotal)}</p>
            <p className="text-xs text-muted-foreground">Trasladado - Acreditable</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-4 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Progreso anual</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{progreso}%</p>
            <Progress value={progreso} className="mt-2 h-2" />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-8 animate-fade-in-up stagger-5 shadow-[var(--shadow-warm-sm)]">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Obligaciones del período</CardTitle>
        </CardHeader>
        <CardContent>
          {periodos.length > 0 ? (
            <div className="space-y-2">
              {periodos.slice(0, 10).map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded border p-3">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{p.impuesto}</Badge>
                    <span className="text-sm font-medium">
                      {MES_LABELS[p.numero_periodo] ?? `P${p.numero_periodo}`} {p.ejercicio}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      Límite: {p.fecha_limite}
                    </span>
                    <Badge className={ESTADO_COLORS[p.estado] ?? ""}>
                      {ESTADO_LABELS[p.estado] ?? p.estado}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="h-12 w-12 text-muted-foreground/40" />
              <p className="mt-4 text-sm font-medium text-muted-foreground">
                No hay periodos registrados
              </p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                Sube tus CFDIs y completa el onboarding para generar tus obligaciones fiscales.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
