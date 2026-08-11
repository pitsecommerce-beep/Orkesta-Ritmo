"use client";

import { useState, useCallback } from "react";
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
import { Upload, FileText, CheckCircle, Clock, AlertCircle } from "lucide-react";

const ALLOWED_EXTENSIONS = [".xml", ".pdf", ".csv", ".xlsx"];

const MOCK_DOCS = [
  { id: "1", name: "cfdi_enero_01.xml", type: "CFDI", status: "procesado", date: "2025-01-15", size: "12 KB" },
  { id: "2", name: "cfdi_enero_02.xml", type: "CFDI", status: "procesado", date: "2025-01-20", size: "8 KB" },
  { id: "3", name: "nomina_enero.xml", type: "Nómina", status: "procesado", date: "2025-01-31", size: "15 KB" },
  { id: "4", name: "extracto_bbva_ene.csv", type: "Extracto", status: "pendiente", date: "2025-02-01", size: "45 KB" },
];

const STATUS_MAP: Record<string, { label: string; icon: typeof CheckCircle; color: string }> = {
  procesado: { label: "Procesado", icon: CheckCircle, color: "text-green-600" },
  pendiente: { label: "Pendiente", icon: Clock, color: "text-yellow-600" },
  error: { label: "Error", icon: AlertCircle, color: "text-red-600" },
};

export default function DocumentosPage() {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Documentos</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sube tus CFDI (XML), estados de cuenta y comprobantes.
        </p>
      </div>

      {/* Upload zone */}
      <Card className="mt-6 animate-fade-in-up stagger-2">
        <CardContent className="pt-6">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
              dragOver ? "border-[var(--color-azul)] bg-[var(--color-azul)]/5" : "border-muted-foreground/25"
            }`}
          >
            <Upload className="h-10 w-10 text-muted-foreground" />
            <p className="mt-4 font-heading font-semibold">
              Arrastra tus archivos aquí
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              o haz clic para seleccionar
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Formatos aceptados: {ALLOWED_EXTENSIONS.join(", ")} — Máximo 10 MB por archivo
            </p>
            <Button variant="outline" className="mt-4 gap-2">
              <Upload className="h-4 w-4" /> Seleccionar archivos
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document list */}
      <Card className="mt-6 animate-fade-in-up stagger-4">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Archivos subidos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Archivo</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead className="text-right">Tamaño</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {MOCK_DOCS.map((doc) => {
                  const st = STATUS_MAP[doc.status] ?? STATUS_MAP.pendiente;
                  return (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{doc.name}</span>
                        </div>
                      </TableCell>
                      <TableCell><Badge variant="outline">{doc.type}</Badge></TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <st.icon className={`h-4 w-4 ${st.color}`} />
                          <span className="text-sm">{st.label}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">{doc.date}</TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">{doc.size}</TableCell>
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
