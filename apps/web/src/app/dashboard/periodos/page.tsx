"use client";

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
import Link from "next/link";
import { formatMXN } from "@/lib/utils";

const MONTHS = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

const MOCK_PERIODS = MONTHS.map((m, i) => ({
  id: String(i + 1),
  month: `${m} 2025`,
  status: i < 1 ? "presentado" : i < 2 ? "preparado" : i < 3 ? "calculado" : "borrador",
  isr: i < 3 ? 800 + Math.round(Math.random() * 500) : 0,
  iva: i < 3 ? 2000 + Math.round(Math.random() * 1500) : 0,
  cfdis: i < 3 ? 5 + Math.floor(Math.random() * 20) : 0,
}));

const STATUS_MAP: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  borrador: { label: "Borrador", variant: "outline" },
  calculado: { label: "Calculado", variant: "secondary" },
  preparado: { label: "Preparado", variant: "default" },
  presentado: { label: "Presentado", variant: "default" },
};

export default function PeriodosPage() {
  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Períodos fiscales</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ejercicio 2025</p>
      </div>

      <Card className="mt-6 animate-fade-in-up stagger-2">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Obligaciones mensuales</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Período</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">ISR</TableHead>
                  <TableHead className="text-right">IVA</TableHead>
                  <TableHead className="text-right">CFDIs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {MOCK_PERIODS.map((p) => {
                  const badge = STATUS_MAP[p.status] ?? { label: p.status, variant: "outline" as const };
                  return (
                    <TableRow key={p.id}>
                      <TableCell>
                        <Link href={`/dashboard/periodos/${p.id}`} className="font-medium text-[var(--color-azul)] hover:underline">
                          {p.month}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant={badge.variant}>{badge.label}</Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono">{p.isr ? formatMXN(p.isr) : "—"}</TableCell>
                      <TableCell className="text-right font-mono">{p.iva ? formatMXN(p.iva) : "—"}</TableCell>
                      <TableCell className="text-right">{p.cfdis || "—"}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
