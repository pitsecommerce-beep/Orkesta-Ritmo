"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
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
  AlertTriangle,
} from "lucide-react";
import { formatMXN } from "@/lib/utils";

const MOCK_CFDIS = [
  { uuid: "ABC12345", emisor: "Proveedor A", rfc: "PAA010101AAA", subtotal: 10000.0, iva_trasladado: 1600.0, isr_retenido: 0, tipo: "I", metodo_pago: "PUE" },
  { uuid: "DEF67890", emisor: "Cliente B", rfc: "CLB020202BBB", subtotal: 25000.0, iva_trasladado: 4000.0, isr_retenido: 250.0, tipo: "I", metodo_pago: "PUE" },
  { uuid: "GHI11111", emisor: "Freelance C", rfc: "FRC030303CCC", subtotal: 8000.0, iva_trasladado: 1280.0, isr_retenido: 80.0, tipo: "I", metodo_pago: "PPD" },
  { uuid: "JKL22222", emisor: "Empresa D", rfc: "EMD040404DDD", subtotal: 15000.0, iva_trasladado: 2400.0, isr_retenido: 150.0, tipo: "I", metodo_pago: "PUE" },
];

const MOCK_DESGLOSE = {
  ingresos_acumulados: 58000.0,
  tasa_resico: 1.5,
  isr_causado: 870.0,
  isr_retenido: 480.0,
  isr_a_cargo: 390.0,
  iva_trasladado: 9280.0,
  iva_acreditable: 0.0,
  iva_retenido: 0.0,
  iva_a_cargo: 9280.0,
};

export default function PeriodoDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/dashboard/periodos">
          <Button variant="ghost" size="sm" className="gap-1">
            <ArrowLeft className="h-4 w-4" /> Períodos
          </Button>
        </Link>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="font-heading text-2xl font-bold">Enero 2025</h1>
          <p className="text-sm text-muted-foreground">Período {id} — RESICO Persona Física</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary">Calculado</Badge>
          <Button className="gap-2">
            <Calculator className="h-4 w-4" /> Recalcular
          </Button>
          <Button variant="outline" className="gap-2">
            <CheckCircle className="h-4 w-4" /> Marcar presentado
          </Button>
        </div>
      </div>

      <Tabs defaultValue="desglose">
        <TabsList>
          <TabsTrigger value="desglose">Desglose fiscal</TabsTrigger>
          <TabsTrigger value="cfdis">CFDIs ({MOCK_CFDIS.length})</TabsTrigger>
          <TabsTrigger value="conciliacion">Conciliación</TabsTrigger>
        </TabsList>

        {/* Tax Breakdown Tab */}
        <TabsContent value="desglose" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* ISR */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--color-azul)]" />
                  ISR — Pago definitivo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Row label="Ingresos acumulados" value={formatMXN(MOCK_DESGLOSE.ingresos_acumulados)} />
                  <Row label={`Tasa RESICO (${MOCK_DESGLOSE.tasa_resico}%)`} value={`${MOCK_DESGLOSE.tasa_resico}%`} />
                  <Separator />
                  <Row label="ISR causado" value={formatMXN(MOCK_DESGLOSE.isr_causado)} bold />
                  <Row label="(-) ISR retenido" value={formatMXN(MOCK_DESGLOSE.isr_retenido)} />
                  <Separator />
                  <Row
                    label="ISR a cargo"
                    value={formatMXN(MOCK_DESGLOSE.isr_a_cargo)}
                    bold
                    highlight
                  />
                </div>
              </CardContent>
            </Card>

            {/* IVA */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--color-azul)]" />
                  IVA — Determinación mensual
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Row label="IVA trasladado cobrado" value={formatMXN(MOCK_DESGLOSE.iva_trasladado)} />
                  <Row label="(-) IVA acreditable pagado" value={formatMXN(MOCK_DESGLOSE.iva_acreditable)} />
                  <Row label="(-) IVA retenido" value={formatMXN(MOCK_DESGLOSE.iva_retenido)} />
                  <Separator />
                  <Row
                    label="IVA a cargo"
                    value={formatMXN(MOCK_DESGLOSE.iva_a_cargo)}
                    bold
                    highlight
                  />
                  {MOCK_DESGLOSE.iva_acreditable === 0 && (
                    <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-xs text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span>
                        IVA acreditable en cero: no se acreditó IVA porque no se pudo comprobar
                        el pago efectivo de las facturas de gastos.
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* CFDIs Tab */}
        <TabsContent value="cfdis" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-heading text-lg">
                CFDIs del período — Trazabilidad
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>UUID</TableHead>
                      <TableHead>Emisor</TableHead>
                      <TableHead>RFC</TableHead>
                      <TableHead className="text-right">Subtotal</TableHead>
                      <TableHead className="text-right">IVA trasladado</TableHead>
                      <TableHead className="text-right">ISR retenido</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Método</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {MOCK_CFDIS.map((c) => (
                      <TableRow key={c.uuid}>
                        <TableCell className="font-mono text-xs">{c.uuid}</TableCell>
                        <TableCell>{c.emisor}</TableCell>
                        <TableCell className="font-mono text-xs">{c.rfc}</TableCell>
                        <TableCell className="text-right font-mono">{formatMXN(c.subtotal)}</TableCell>
                        <TableCell className="text-right font-mono">{formatMXN(c.iva_trasladado)}</TableCell>
                        <TableCell className="text-right font-mono">{formatMXN(c.isr_retenido)}</TableCell>
                        <TableCell><Badge variant="outline">{c.tipo}</Badge></TableCell>
                        <TableCell><Badge variant="secondary">{c.metodo_pago}</Badge></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conciliation Tab */}
        <TabsContent value="conciliacion" className="mt-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-base">CFDIs emitidos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {MOCK_CFDIS.map((c) => (
                    <div key={c.uuid} className="flex items-center justify-between rounded border p-3 text-sm">
                      <div>
                        <p className="font-medium">{c.emisor}</p>
                        <p className="text-xs text-muted-foreground font-mono">{c.uuid}</p>
                      </div>
                      <span className="font-mono">{formatMXN(c.subtotal)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-base">Movimientos bancarios</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                  No hay extractos bancarios cargados para este período.
                  <br />
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

function Row({
  label,
  value,
  bold,
  highlight,
}: {
  label: string;
  value: string;
  bold?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between ${highlight ? "rounded-md bg-[var(--color-azul)]/5 px-3 py-2" : ""}`}>
      <span className={`text-sm ${bold ? "font-semibold" : "text-muted-foreground"}`}>{label}</span>
      <span className={`font-mono text-sm ${bold ? "font-bold" : ""} ${highlight ? "text-[var(--color-azul)] text-base" : ""}`}>
        {value}
      </span>
    </div>
  );
}
