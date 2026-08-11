"use client";

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
import { FileText, Search } from "lucide-react";
import { formatMXN } from "@/lib/utils";
import { useState } from "react";

const MOCK_CFDIS = [
  { uuid: "ABC12345-1111-2222-3333-444455556666", emisor_nombre: "Proveedor A", emisor_rfc: "PAA010101AAA", receptor_rfc: "XXXX010101AAA", subtotal: 10000.0, total: 11600.0, tipo: "I", metodo_pago: "PUE", fecha: "2025-01-15", periodo: "Enero 2025", actividad: "Servicios profesionales" },
  { uuid: "DEF67890-1111-2222-3333-444455556666", emisor_nombre: "Cliente B", emisor_rfc: "CLB020202BBB", receptor_rfc: "XXXX010101AAA", subtotal: 25000.0, total: 29000.0, tipo: "I", metodo_pago: "PUE", fecha: "2025-01-20", periodo: "Enero 2025", actividad: "Venta de mercancías" },
  { uuid: "GHI11111-1111-2222-3333-444455556666", emisor_nombre: "Freelance C", emisor_rfc: "FRC030303CCC", receptor_rfc: "XXXX010101AAA", subtotal: 8000.0, total: 9280.0, tipo: "I", metodo_pago: "PPD", fecha: "2025-02-10", periodo: "Febrero 2025", actividad: "Sin asignar" },
  { uuid: "JKL22222-1111-2222-3333-444455556666", emisor_nombre: "Empresa D", emisor_rfc: "EMD040404DDD", receptor_rfc: "XXXX010101AAA", subtotal: 15000.0, total: 17400.0, tipo: "I", metodo_pago: "PUE", fecha: "2025-02-15", periodo: "Febrero 2025", actividad: "Arrendamiento" },
  { uuid: "MNO33333-1111-2222-3333-444455556666", emisor_nombre: "Nómina Corp", emisor_rfc: "NCO050505EEE", receptor_rfc: "XXXX010101AAA", subtotal: 20000.0, total: 20000.0, tipo: "N", metodo_pago: "PUE", fecha: "2025-01-31", periodo: "Enero 2025", actividad: "Sueldos" },
];

export default function CfdisPage() {
  const [filter, setFilter] = useState("");
  const [tipoCfdi, setTipoCfdi] = useState("todos");

  const filtered = MOCK_CFDIS.filter((c) => {
    const matchesSearch = !filter || c.emisor_nombre.toLowerCase().includes(filter.toLowerCase()) || c.uuid.includes(filter);
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

      {/* Filters */}
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
            <SelectItem value="N">Nómina</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card className="mt-6 animate-fade-in-up stagger-3">
        <CardHeader>
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {filtered.length} comprobantes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>UUID</TableHead>
                  <TableHead>Emisor</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Método</TableHead>
                  <TableHead>Período</TableHead>
                  <TableHead>Actividad</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((c) => (
                  <TableRow key={c.uuid}>
                    <TableCell className="font-mono text-xs max-w-[120px] truncate">{c.uuid.split("-")[0]}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium text-sm">{c.emisor_nombre}</p>
                        <p className="text-xs text-muted-foreground font-mono">{c.emisor_rfc}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">{c.fecha}</TableCell>
                    <TableCell className="text-right font-mono">{formatMXN(c.total)}</TableCell>
                    <TableCell><Badge variant="outline">{c.tipo}</Badge></TableCell>
                    <TableCell><Badge variant="secondary">{c.metodo_pago}</Badge></TableCell>
                    <TableCell className="text-sm">{c.periodo}</TableCell>
                    <TableCell>
                      {c.actividad === "Sin asignar" ? (
                        <Button variant="outline" size="sm" className="text-xs">Asignar</Button>
                      ) : (
                        <span className="text-sm">{c.actividad}</span>
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
