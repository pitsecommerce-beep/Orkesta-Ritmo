"use client";

import { use } from "react";
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
} from "lucide-react";

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

      <div className="animate-fade-in-up flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="font-heading text-2xl font-bold">Período {id}</h1>
          <p className="text-sm text-muted-foreground">Sin datos — Sube CFDIs para calcular</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline">Sin datos</Badge>
          <Button className="gap-2" disabled>
            <Calculator className="h-4 w-4" /> Recalcular
          </Button>
          <Button variant="outline" className="gap-2" disabled>
            <CheckCircle className="h-4 w-4" /> Marcar presentado
          </Button>
        </div>
      </div>

      <Tabs defaultValue="desglose">
        <TabsList>
          <TabsTrigger value="desglose">Desglose fiscal</TabsTrigger>
          <TabsTrigger value="cfdis">CFDIs (0)</TabsTrigger>
          <TabsTrigger value="conciliacion">Conciliación</TabsTrigger>
        </TabsList>

        {/* Tax Breakdown Tab */}
        <TabsContent value="desglose" className="mt-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--color-azul)]" />
                  ISR — Pago definitivo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyDesglose />
              </CardContent>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-[var(--color-azul)]" />
                  IVA — Determinación mensual
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyDesglose />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* CFDIs Tab */}
        <TabsContent value="cfdis" className="mt-6 animate-fade-in">
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
                    <TableRow>
                      <TableCell colSpan={8}>
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                          <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
                          <p className="mt-3 text-sm text-muted-foreground">
                            No hay CFDIs para este período
                          </p>
                          <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                            Sube tus archivos XML de CFDIs para ver el desglose completo.
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conciliation Tab */}
        <TabsContent value="conciliacion" className="mt-6 animate-fade-in">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-base">CFDIs emitidos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                  No hay CFDIs registrados para este período.
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
