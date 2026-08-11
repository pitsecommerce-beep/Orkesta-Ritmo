"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import Link from "next/link";
import {
  Calendar,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
} from "lucide-react";
import { formatMXN } from "@/lib/utils";

const MOCK_PERIODS = [
  { id: "1", month: "Enero 2025", status: "presentado", isr: 1250.0, iva: 3200.0 },
  { id: "2", month: "Febrero 2025", status: "preparado", isr: 980.5, iva: 2800.0 },
  { id: "3", month: "Marzo 2025", status: "calculado", isr: 1100.0, iva: 3100.0 },
  { id: "4", month: "Abril 2025", status: "borrador", isr: 0, iva: 0 },
];

const STATUS_BADGES: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  borrador: { label: "Borrador", variant: "outline" },
  calculado: { label: "Calculado", variant: "secondary" },
  contrastado: { label: "Contrastado", variant: "secondary" },
  preparado: { label: "Preparado", variant: "default" },
  presentado: { label: "Presentado", variant: "default" },
  cerrado: { label: "Cerrado", variant: "default" },
  con_diferencia: { label: "Con diferencia", variant: "destructive" },
  requiere_revision: { label: "Requiere revisión", variant: "destructive" },
};

export default function DashboardHome() {
  const pending = MOCK_PERIODS.filter((p) => !["presentado", "cerrado"].includes(p.status));

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up mb-8">
        <h1 className="font-heading text-2xl font-bold">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ejercicio 2025 — RESICO Persona Física</p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="animate-fade-in-up stagger-1 card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Períodos pendientes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{pending.length}</p>
            <p className="text-xs text-muted-foreground">de {MOCK_PERIODS.length} obligaciones</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-2 card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">ISR acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatMXN(MOCK_PERIODS.reduce((s, p) => s + p.isr, 0))}</p>
            <p className="text-xs text-muted-foreground">Pagos definitivos</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-3 card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">IVA acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatMXN(MOCK_PERIODS.reduce((s, p) => s + p.iva, 0))}</p>
            <p className="text-xs text-muted-foreground">Trasladado - Acreditable</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-4 card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Progreso anual</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {Math.round((MOCK_PERIODS.filter((p) => p.status === "presentado").length / 12) * 100)}%
            </p>
            <Progress
              value={(MOCK_PERIODS.filter((p) => p.status === "presentado").length / 12) * 100}
              className="mt-2 h-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Pending obligations */}
      <Card className="mt-8 animate-fade-in-up stagger-5">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Obligaciones del período</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {MOCK_PERIODS.map((p) => {
              const badge = STATUS_BADGES[p.status] ?? { label: p.status, variant: "outline" as const };
              return (
                <Link
                  key={p.id}
                  href={`/dashboard/periodos/${p.id}`}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-all hover:shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    {p.status === "presentado" ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : p.status === "borrador" ? (
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    ) : (
                      <Clock className="h-5 w-5 text-[var(--color-azul)]" />
                    )}
                    <div>
                      <p className="font-medium">{p.month}</p>
                      <p className="text-xs text-muted-foreground">
                        ISR: {formatMXN(p.isr)} · IVA: {formatMXN(p.iva)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={badge.variant}>{badge.label}</Badge>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
