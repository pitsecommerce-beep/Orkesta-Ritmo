"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FolderOpen, Loader2 } from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";

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
  { id: "m3", impuesto: "ISR", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 2, fecha_limite: "2025-03-17", estado: "calculado", resultado_json: { isr_a_cargo: 2100 } },
  { id: "m4", impuesto: "IVA", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 2, fecha_limite: "2025-03-17", estado: "borrador", resultado_json: null },
  { id: "m5", impuesto: "ISR", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 3, fecha_limite: "2025-04-17", estado: "borrador", resultado_json: null },
  { id: "m6", impuesto: "IVA", tipo_periodo: "mensual", ejercicio: 2025, numero_periodo: 3, fecha_limite: "2025-04-17", estado: "borrador", resultado_json: null },
];

export default function PeriodosPage() {
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

  function getAmount(p: PeriodoRow): number {
    if (!p.resultado_json) return 0;
    if (p.impuesto === "ISR") return Number(p.resultado_json.isr_a_cargo) || 0;
    if (p.impuesto === "IVA") return Number(p.resultado_json.iva_determinado) || 0;
    return 0;
  }

  const ejercicio = periodos.length > 0 ? periodos[0].ejercicio : new Date().getFullYear();

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Periodos fiscales</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ejercicio {ejercicio}</p>
      </div>

      <Card className="mt-6 animate-fade-in-up stagger-2">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Obligaciones mensuales</CardTitle>
        </CardHeader>
        <CardContent>
          {loading || tenantLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : periodos.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Periodo</TableHead>
                    <TableHead>Impuesto</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Fecha límite</TableHead>
                    <TableHead className="text-right">Monto</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {periodos.map((p) => (
                    <TableRow key={p.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell>
                        <Link href={`/dashboard/periodos/${p.id}`} className="font-medium text-sm hover:underline">
                          {MES_LABELS[p.numero_periodo] ?? `P${p.numero_periodo}`} {p.ejercicio}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{p.impuesto}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={ESTADO_COLORS[p.estado] ?? ""}>
                          {ESTADO_LABELS[p.estado] ?? p.estado}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{p.fecha_limite}</TableCell>
                      <TableCell className="text-right font-mono">
                        {getAmount(p) > 0 ? formatMXN(getAmount(p)) : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">
                No hay periodos registrados
              </p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                Los periodos se generan automáticamente al completar el onboarding y subir tus CFDIs.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
