"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Calendar,
  FileText,
  Clock,
  FolderOpen,
} from "lucide-react";
import { formatMXN } from "@/lib/utils";

export default function DashboardHome() {
  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up mb-8">
        <h1 className="font-heading text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ejercicio 2025 — RESICO Persona Física</p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="animate-fade-in-up stagger-1 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Períodos pendientes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">0</p>
            <p className="text-xs text-muted-foreground">de 0 obligaciones</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-2 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">ISR acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{formatMXN(0)}</p>
            <p className="text-xs text-muted-foreground">Pagos definitivos</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-3 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">IVA acumulado</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">{formatMXN(0)}</p>
            <p className="text-xs text-muted-foreground">Trasladado - Acreditable</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-in-up stagger-4 card-hover shadow-[var(--shadow-warm-sm)]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Progreso anual</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold font-mono">0%</p>
            <Progress value={0} className="mt-2 h-2" />
          </CardContent>
        </Card>
      </div>

      {/* Empty state */}
      <Card className="mt-8 animate-fade-in-up stagger-5 shadow-[var(--shadow-warm-sm)]">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Obligaciones del período</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FolderOpen className="h-12 w-12 text-muted-foreground/40" />
            <p className="mt-4 text-sm font-medium text-muted-foreground">
              No hay períodos registrados
            </p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground/70">
              Sube tus CFDIs y completa el onboarding para generar tus obligaciones fiscales.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
