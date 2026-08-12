"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FolderOpen } from "lucide-react";

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
                <TableRow>
                  <TableCell colSpan={5}>
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <FolderOpen className="h-10 w-10 text-muted-foreground/40" />
                      <p className="mt-3 text-sm text-muted-foreground">
                        No hay períodos registrados
                      </p>
                      <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
                        Los períodos se generan automáticamente al completar el onboarding y subir tus CFDIs.
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
