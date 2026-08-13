"use client";

import { useEffect, useState } from "react";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { FileText, Search, FolderOpen, Loader2 } from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";

interface CfdiRow {
  id: string;
  uuid_fiscal: string;
  nombre_emisor: string | null;
  rfc_emisor: string;
  rfc_receptor: string;
  subtotal: number;
  total: number;
  tipo: string;
  metodo_pago: string | null;
  fecha_emision: string;
  actividad_id: string | null;
}

const MOCK_CFDIS: CfdiRow[] = [
  { id: "1", uuid_fiscal: "ABC12345-1111-2222-3333-444455556666", nombre_emisor: "Proveedor A", rfc_emisor: "PAA010101AAA", rfc_receptor: "XXXX010101AAA", subtotal: 10000.0, total: 11600.0, tipo: "I", metodo_pago: "PUE", fecha_emision: "2025-01-15T00:00:00", actividad_id: "act1" },
  { id: "2", uuid_fiscal: "DEF67890-1111-2222-3333-444455556666", nombre_emisor: "Cliente B", rfc_emisor: "CLB020202BBB", rfc_receptor: "XXXX010101AAA", subtotal: 25000.0, total: 29000.0, tipo: "I", metodo_pago: "PUE", fecha_emision: "2025-01-20T00:00:00", actividad_id: "act2" },
  { id: "3", uuid_fiscal: "GHI11111-1111-2222-3333-444455556666", nombre_emisor: "Freelance C", rfc_emisor: "FRC030303CCC", rfc_receptor: "XXXX010101AAA", subtotal: 8000.0, total: 9280.0, tipo: "I", metodo_pago: "PPD", fecha_emision: "2025-02-10T00:00:00", actividad_id: null },
  { id: "4", uuid_fiscal: "JKL22222-1111-2222-3333-444455556666", nombre_emisor: "Empresa D", rfc_emisor: "EMD040404DDD", rfc_receptor: "XXXX010101AAA", subtotal: 15000.0, total: 17400.0, tipo: "I", metodo_pago: "PUE", fecha_emision: "2025-02-15T00:00:00", actividad_id: "act3" },
  { id: "5", uuid_fiscal: "MNO33333-1111-2222-3333-444455556666", nombre_emisor: "Nomina Corp", rfc_emisor: "NCO050505EEE", rfc_receptor: "XXXX010101AAA", subtotal: 20000.0, total: 20000.0, tipo: "N", metodo_pago: "PUE", fecha_emision: "2025-01-31T00:00:00", actividad_id: "act4" },
];

export default function CfdisPage() {
  const { demoMode } = useDemoMode();
  const { tenant, loading: tenantLoading } = useTenant();
  const [cfdis, setCfdis] = useState<CfdiRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [tipoCfdi, setTipoCfdi] = useState("todos");

  useEffect(() => {
    if (demoMode) {
      setCfdis(MOCK_CFDIS);
      setLoading(false);
      return;
    }

    if (tenantLoading) return;

    async function load() {
      if (!tenant) { setLoading(false); return; }

      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data } = await supabase
        .from("cfdis")
        .select("id, uuid_fiscal, nombre_emisor, rfc_emisor, rfc_receptor, subtotal, total, tipo, metodo_pago, fecha_emision, actividad_id")
        .eq("tenant_id", tenant.tenantId)
        .order("fecha_emision", { ascending: false })
        .limit(100);

      setCfdis((data ?? []) as CfdiRow[]);
      setLoading(false);
    }
    load();
  }, [demoMode, tenant, tenantLoading]);

  const filtered = cfdis.filter((c) => {
    const matchesSearch = !filter ||
      (c.nombre_emisor ?? "").toLowerCase().includes(filter.toLowerCase()) ||
      c.uuid_fiscal.includes(filter);
    const matchesTipo = tipoCfdi === "todos" || c.tipo === tipoCfdi;
    return matchesSearch && matchesTipo;
  });

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">CFDIs</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Comprobantes fiscales digitales clasificados y verificados.
        </p>
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row animate-fade-in-up stagger-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por emisor o UUID..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={tipoCfdi} onValueChange={setTipoCfdi}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los tipos</SelectItem>
            <SelectItem value="I">Ingreso</SelectItem>
            <SelectItem value="E">Egreso</SelectItem>
            <SelectItem value="P">Pago</SelectItem>
            <SelectItem value="N">Nomina</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="mt-6 animate-fade-in-up stagger-3">
        <CardHeader>
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {loading || tenantLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              `${filtered.length} comprobantes`
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading || tenantLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filtered.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>UUID</TableHead>
                    <TableHead>Emisor</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Metodo</TableHead>
                    <TableHead>Actividad</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-mono text-xs max-w-[120px] truncate">
                        {c.uuid_fiscal.split("-")[0]}
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm">{c.nombre_emisor ?? "—"}</p>
                          <p className="text-xs text-muted-foreground font-mono">{c.rfc_emisor}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {c.fecha_emision.split("T")[0]}
                      </TableCell>
                      <TableCell className="text-right font-mono">{formatMXN(c.total)}</TableCell>
                      <TableCell><Badge variant="outline">{c.tipo}</Badge></TableCell>
                      <TableCell><Badge variant="secondary">{c.metodo_pago ?? "—"}</Badge></TableCell>
                      <TableCell>
                        {c.actividad_id ? (
                          <span className="text-sm">Asignada</span>
                        ) : (
                          <Button variant="outline" size="sm" className="text-xs">Asignar</Button>
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
              <p className="mt-3 text-sm text-muted-foreground">No hay CFDIs registrados</p>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                Sube tus archivos XML para ver tus comprobantes fiscales.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
