"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ArrowLeft,
  Calculator,
  CheckCircle,
  FileText,
  FolderOpen,
  Loader2,
} from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { usePermissions } from "@/hooks/use-permissions";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

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
  presentado: "bg-green-100 text-green-700",
  cerrado: "bg-green-200 text-green-800",
  con_diferencia: "bg-yellow-100 text-yellow-700",
  requiere_revision: "bg-red-100 text-red-700",
};

const MES_LABELS = [
  "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

interface PeriodoData {
  id: string;
  impuesto: string;
  tipo_periodo: string;
  ejercicio: number;
  numero_periodo: number;
  fecha_limite: string;
  estado: string;
  resultado_json: Record<string, unknown> | null;
}

interface CfdiRow {
  id: string;
  uuid_fiscal: string;
  nombre_emisor: string | null;
  rfc_emisor: string;
  subtotal: number;
  total: number;
  tipo: string;
  metodo_pago: string | null;
}

export default function PeriodoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { demoMode } = useDemoMode();
  const { canCalculate } = usePermissions();
  const [periodo, setPeriodo] = useState<PeriodoData | null>(null);
  const [cfdis, setCfdis] = useState<CfdiRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (demoMode) {
      setPeriodo({
        id,
        impuesto: "ISR",
        tipo_periodo: "mensual",
        ejercicio: 2025,
        numero_periodo: 1,
        fecha_limite: "2025-02-17",
        estado: "presentado",
        resultado_json: {
          isr_a_cargo: 1250,
          ingresos_gravados: 35000,
          tasa_aplicada: 0.0125,
          ingresos_periodo: 35000,
        },
      });
      setCfdis([
        { id: "d1", uuid_fiscal: "ABC12345-1111-2222-3333-444455556666", nombre_emisor: "Proveedor A", rfc_emisor: "PAA010101AAA", subtotal: 10000, total: 11600, tipo: "I", metodo_pago: "PUE" },
        { id: "d2", uuid_fiscal: "DEF67890-1111-2222-3333-444455556666", nombre_emisor: "Cliente B", rfc_emisor: "CLB020202BBB", subtotal: 25000, total: 29000, tipo: "I", metodo_pago: "PUE" },
      ]);
      setLoading(false);
      return;
    }

    setPeriodo(null);
    setCfdis([]);
    setLoading(true);

    async function load() {
      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data: p } = await supabase
        .from("periodos")
        .select("id, impuesto, tipo_periodo, ejercicio, numero_periodo, fecha_limite, estado, resultado_json")
        .eq("id", id)
        .maybeSingle();

      if (p) {
        setPeriodo(p as PeriodoData);

        const { data: c } = await supabase
          .from("cfdis")
          .select("id, uuid_fiscal, nombre_emisor, rfc_emisor, subtotal, total, tipo, metodo_pago")
          .eq("periodo_id", id)
          .order("fecha_emision", { ascending: false });

        setCfdis((c ?? []) as CfdiRow[]);
      }

      setLoading(false);
    }
    load();
  }, [id, demoMode]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const label = periodo
    ? `${MES_LABELS[periodo.numero_periodo] ?? `P${periodo.numero_periodo}`} ${periodo.ejercicio} — ${periodo.impuesto}`
    : `Periodo ${id}`;

  const subtitle = periodo
    ? `${periodo.tipo_periodo} — Límite: ${periodo.fecha_limite}`
    : "Sin datos";

  const canRecalculate = periodo && !["presentado", "cerrado"].includes(periodo.estado);
  const canMarkPresented = periodo && periodo.estado === "preparado";

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/dashboard/periodos">
          <Button variant="ghost" size="sm" className="gap-1">
            <ArrowLeft className="h-4 w-4" /> Periodos
          </Button>
        </Link>
      </div>

      <div className="animate-fade-in-up flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="font-heading text-2xl font-bold">{label}</h1>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        <div className="flex items-center gap-3">
          {periodo && (
            <Badge className={ESTADO_COLORS[periodo.estado] ?? ""}>
              {ESTADO_LABELS[periodo.estado] ?? periodo.estado}
            </Badge>
          )}
          {canCalculate ? (
            <Button className="gap-2" disabled={!canRecalculate}>
              <Calculator className="h-4 w-4" /> Recalcular
            </Button>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={0}>
                  <Button className="gap-2" disabled>
                    <Calculator className="h-4 w-4" /> Recalcular
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                Tu rol de lectura no permite recalcular periodos.
              </TooltipContent>
            </Tooltip>
          )}
          {canCalculate ? (
            <Button variant="outline" className="gap-2" disabled={!canMarkPresented}>
              <CheckCircle className="h-4 w-4" /> Marcar presentado
            </Button>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={0}>
                  <Button variant="outline" className="gap-2" disabled>
                    <CheckCircle className="h-4 w-4" /> Marcar presentado
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                Tu rol de lectura no permite marcar periodos como presentados.
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>

      <Tabs defaultValue="desglose">
        <TabsList>
          <TabsTrigger value="desglose">Desglose fiscal</TabsTrigger>
          <TabsTrigger value="cfdis">CFDIs ({cfdis.length})</TabsTrigger>
          <TabsTrigger value="conciliacion">Conciliación</TabsTrigger>
        </TabsList>

        <TabsContent value="desglose" className="mt-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--color-azul)]" />
                  {periodo?.impuesto === "IVA" ? "IVA — Determinación mensual" : "ISR — Desglose del periodo"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {periodo?.resultado_json ? (
                  <div className="space-y-3">
                    {Object.entries(periodo.resultado_json).map(([key, val]) => (
                      <div key={key} className="flex items-center justify-between border-b pb-2 last:border-0">
                        <span className="text-sm text-muted-foreground capitalize">
                          {key.replace(/_/g, " ")}
                        </span>
                        <span className="font-mono text-sm font-medium">
                          {typeof val === "number" ? (val < 1 ? `${(val * 100).toFixed(2)}%` : formatMXN(val)) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyDesglose />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="cfdis" className="mt-6 animate-fade-in">
          <Card>
            <CardHeader>
              <CardTitle className="font-heading text-lg">
                CFDIs del periodo — Trazabilidad
              </CardTitle>
            </CardHeader>
            <CardContent>
              {cfdis.length > 0 ? (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>UUID</TableHead>
                        <TableHead>Emisor</TableHead>
                        <TableHead>RFC</TableHead>
                        <TableHead className="text-right">Subtotal</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Método</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cfdis.map((c) => (
                        <TableRow key={c.id}>
                          <TableCell className="font-mono text-xs max-w-[120px] truncate">
                            {c.uuid_fiscal.split("-")[0]}
                          </TableCell>
                          <TableCell className="text-sm">{c.nombre_emisor ?? "—"}</TableCell>
                          <TableCell className="font-mono text-xs">{c.rfc_emisor}</TableCell>
                          <TableCell className="text-right font-mono">{formatMXN(c.subtotal)}</TableCell>
                          <TableCell className="text-right font-mono">{formatMXN(c.total)}</TableCell>
                          <TableCell><Badge variant="outline">{c.tipo}</Badge></TableCell>
                          <TableCell><Badge variant="secondary">{c.metodo_pago ?? "—"}</Badge></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
                  <p className="mt-3 text-sm text-muted-foreground">
                    No hay CFDIs para este periodo
                  </p>
                  <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                    Sube tus archivos XML de CFDIs para ver el desglose completo.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conciliacion" className="mt-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-base">CFDIs emitidos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                  {cfdis.length > 0
                    ? `${cfdis.length} CFDI(s) vinculados a este periodo.`
                    : "No hay CFDIs registrados para este periodo."}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-base">Movimientos bancarios</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                  No hay extractos bancarios cargados para este periodo.
                  <Link href="/dashboard/extractos" className="text-[var(--color-azul)] underline ml-1">
                    Subir extracto
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function EmptyDesglose() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <FolderOpen className="h-8 w-8 text-muted-foreground/40" />
      <p className="mt-3 text-sm text-muted-foreground">
        Sin cálculo disponible
      </p>
      <p className="mt-1 text-xs text-muted-foreground/70">
        Sube CFDIs para generar el desglose fiscal.
      </p>
    </div>
  );
}
