"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Upload, Building2, CheckCircle, AlertTriangle } from "lucide-react";
import { formatMXN } from "@/lib/utils";

const MOCK_MOVEMENTS = [
  { id: "1", fecha: "2025-01-05", concepto: "Transferencia recibida - PAA010101AAA", monto: 11600.0, tipo: "abono", conciliado: true, espejo: false },
  { id: "2", fecha: "2025-01-10", concepto: "Comisión bancaria", monto: -150.0, tipo: "cargo", conciliado: false, espejo: false },
  { id: "3", fecha: "2025-01-15", concepto: "Transferencia recibida - CLB020202BBB", monto: 29000.0, tipo: "abono", conciliado: true, espejo: false },
  { id: "4", fecha: "2025-01-15", concepto: "Movimiento espejo - reverso comisión", monto: 150.0, tipo: "abono", conciliado: false, espejo: true },
  { id: "5", fecha: "2025-01-15", concepto: "Cargo espejo - reverso comisión", monto: -150.0, tipo: "cargo", conciliado: false, espejo: true },
  { id: "6", fecha: "2025-01-20", concepto: "Pago servicios", monto: -3500.0, tipo: "cargo", conciliado: false, espejo: false },
  { id: "7", fecha: "2025-01-25", concepto: "Dinero retenido - Mercado Pago", monto: -800.0, tipo: "cargo", conciliado: false, espejo: false },
  { id: "8", fecha: "2025-01-31", concepto: "Liberación retenido", monto: 800.0, tipo: "abono", conciliado: false, espejo: false },
];

export default function ExtractosPage() {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Extractos bancarios</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sube estados de cuenta para conciliar contra tus CFDIs.
        </p>
      </div>

      {/* Upload */}
      <Card className="mt-6 animate-fade-in-up stagger-2">
        <CardContent className="pt-6">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5" : "border-muted-foreground/25"
            }`}
          >
            <Building2 className="h-8 w-8 text-muted-foreground" />
            <p className="mt-3 font-heading font-semibold">Sube tu estado de cuenta</p>
            <p className="mt-1 text-sm text-muted-foreground">CSV o XLSX de Mercado Pago, BBVA, Santander, Nu o Revolut</p>
            <Button variant="outline" className="mt-4 gap-2">
              <Upload className="h-4 w-4" /> Seleccionar archivo
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Movements table */}
      <Card className="mt-6 animate-fade-in-up stagger-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-heading text-lg">Movimientos — Enero 2025</CardTitle>
          <Badge variant="outline">{MOCK_MOVEMENTS.length} movimientos</Badge>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Concepto</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                  <TableHead>Estado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {MOCK_MOVEMENTS.map((m) => (
                  <TableRow key={m.id} className={m.espejo ? "opacity-50" : ""}>
                    <TableCell className="text-sm">{m.fecha}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{m.concepto}</span>
                        {m.espejo && <Badge variant="outline" className="text-xs">Espejo</Badge>}
                      </div>
                    </TableCell>
                    <TableCell className={`text-right font-mono ${m.monto >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {formatMXN(Math.abs(m.monto))}
                      {m.monto < 0 ? " -" : " +"}
                    </TableCell>
                    <TableCell>
                      {m.conciliado ? (
                        <div className="flex items-center gap-1 text-green-600">
                          <CheckCircle className="h-4 w-4" />
                          <span className="text-xs">Conciliado</span>
                        </div>
                      ) : m.espejo ? (
                        <span className="text-xs text-muted-foreground">Ignorado</span>
                      ) : (
                        <div className="flex items-center gap-1 text-yellow-600">
                          <AlertTriangle className="h-4 w-4" />
                          <span className="text-xs">Pendiente</span>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
