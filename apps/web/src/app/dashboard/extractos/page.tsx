"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
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
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { Upload, Building2, CheckCircle, AlertTriangle, FolderOpen, Loader2, ArrowRight } from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";
import { usePermissions } from "@/hooks/use-permissions";

interface MovimientoRow {
  id: string;
  fecha: string;
  descripcion: string;
  monto: number;
  es_espejo: boolean;
  conciliado: boolean;
}

const MOCK_MOVEMENTS: MovimientoRow[] = [
  { id: "1", fecha: "2025-01-05", descripcion: "Transferencia recibida - PAA010101AAA", monto: 11600.0, es_espejo: false, conciliado: true },
  { id: "2", fecha: "2025-01-10", descripcion: "Comisión bancaria", monto: -150.0, es_espejo: false, conciliado: false },
  { id: "3", fecha: "2025-01-15", descripcion: "Transferencia recibida - CLB020202BBB", monto: 29000.0, es_espejo: false, conciliado: true },
  { id: "4", fecha: "2025-01-15", descripcion: "Movimiento espejo - reverso comisión", monto: 150.0, es_espejo: true, conciliado: false },
  { id: "5", fecha: "2025-01-15", descripcion: "Cargo espejo - reverso comisión", monto: -150.0, es_espejo: true, conciliado: false },
  { id: "6", fecha: "2025-01-20", descripcion: "Pago servicios", monto: -3500.0, es_espejo: false, conciliado: false },
  { id: "7", fecha: "2025-01-25", descripcion: "Dinero retenido - Mercado Pago", monto: -800.0, es_espejo: false, conciliado: false },
  { id: "8", fecha: "2025-01-31", descripcion: "Liberación retenido", monto: 800.0, es_espejo: false, conciliado: false },
];

export default function ExtractosPage() {
  const { demoMode } = useDemoMode();
  const { tenant, loading: tenantLoading } = useTenant();
  const { canUpload } = usePermissions();
  const [movimientos, setMovimientos] = useState<MovimientoRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    if (demoMode) {
      setMovimientos(MOCK_MOVEMENTS);
      setLoading(false);
      return;
    }

    setMovimientos([]);
    setLoading(true);

    if (tenantLoading) return;

    async function load() {
      if (!tenant) { setLoading(false); return; }

      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data } = await supabase
        .from("movimientos_bancarios")
        .select("id, fecha, descripcion, monto, es_espejo")
        .eq("tenant_id", tenant.tenantId)
        .order("fecha", { ascending: false })
        .limit(100);

      const rows = (data ?? []).map((m: Record<string, unknown>) => ({
        ...m,
        conciliado: false,
      })) as MovimientoRow[];

      setMovimientos(rows);
      setLoading(false);
    }
    load();
  }, [demoMode, tenant, tenantLoading]);

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-start justify-between animate-fade-in-up">
        <div>
          <h1 className="font-heading text-2xl font-bold">Extractos bancarios</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Sube estados de cuenta para conciliar contra tus CFDIs.
          </p>
        </div>
        {canUpload ? (
          <Link href="/dashboard/documentos">
            <Button variant="outline" className="gap-2">
              <Upload className="h-4 w-4" /> Subir extracto
            </Button>
          </Link>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span tabIndex={0}>
                <Button variant="outline" className="gap-2" disabled>
                  <Upload className="h-4 w-4" /> Subir extracto
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              Tu rol de lectura no permite subir documentos.
            </TooltipContent>
          </Tooltip>
        )}
      </div>

      <Card className="mt-6 animate-fade-in-up stagger-2">
        <CardContent className="pt-6">
          {canUpload ? (
            <Link href="/dashboard/documentos" className="block">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); }}
                className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors cursor-pointer ${
                  dragOver ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5" : "border-muted-foreground/25 hover:border-[var(--color-azul)]/50"
                }`}
              >
                <Building2 className="h-8 w-8 text-muted-foreground" />
                <p className="mt-3 font-heading font-semibold">Sube tu estado de cuenta</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  CSV o XLSX de Mercado Pago, BBVA, Santander, Nu o Revolut
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Haz clic para ir al asistente de carga de documentos
                </p>
              </div>
            </Link>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/15 bg-muted/30 p-8 text-center">
              <Building2 className="h-8 w-8 text-muted-foreground/40" />
              <p className="mt-3 font-heading font-semibold text-muted-foreground">
                Carga de extractos no disponible
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Tu rol de lectura no permite subir documentos. Contacta al propietario del workspace.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6 animate-fade-in-up stagger-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-heading text-lg">Movimientos</CardTitle>
          {!loading && <Badge variant="outline">{movimientos.length} movimientos</Badge>}
        </CardHeader>
        <CardContent>
          {loading || tenantLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : movimientos.length > 0 ? (
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
                  {movimientos.map((m) => (
                    <TableRow key={m.id} className={m.es_espejo ? "opacity-50" : ""}>
                      <TableCell className="text-sm">{m.fecha}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{m.descripcion}</span>
                          {m.es_espejo && <Badge variant="outline" className="text-xs">Espejo</Badge>}
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
                        ) : m.es_espejo ? (
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
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
              <p className="mt-3 text-sm text-muted-foreground">No hay movimientos registrados</p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                Sube un estado de cuenta desde la sección de Documentos para ver tus movimientos bancarios.
              </p>
              {canUpload && (
                <Link href="/dashboard/documentos" className="mt-3">
                  <Button variant="outline" size="sm" className="gap-1.5">
                    Ir a Documentos <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
