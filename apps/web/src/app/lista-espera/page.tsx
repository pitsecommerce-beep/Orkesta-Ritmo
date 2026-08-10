"use client";

import { useState } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle } from "lucide-react";

export default function ListaEsperaPage() {
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <div className="min-h-full">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-4xl items-center px-4">
          <Link href="/"><Logo type="full" /></Link>
        </div>
      </header>
      <main className="mx-auto flex max-w-md flex-col items-center px-4 py-20">
        {sent ? (
          <div className="text-center">
            <CheckCircle className="mx-auto h-12 w-12 text-green-600" />
            <h1 className="mt-4 font-heading text-2xl font-bold">¡Registrado!</h1>
            <p className="mt-2 text-muted-foreground">
              Te avisaremos cuando tu régimen esté disponible en Ritmo.
            </p>
            <Link href="/" className="mt-6 inline-block">
              <Button variant="outline">Volver al inicio</Button>
            </Link>
          </div>
        ) : (
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="font-heading text-xl">Lista de espera</CardTitle>
              <p className="text-sm text-muted-foreground">
                Tu régimen fiscal aún no está soportado. Déjanos tu correo y te notificamos cuando lo esté.
              </p>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="email">Correo electrónico</Label>
                  <Input id="email" type="email" required placeholder="tu@correo.com" className="mt-1" />
                </div>
                <div>
                  <Label htmlFor="regimen">Régimen fiscal</Label>
                  <Input id="regimen" required placeholder="Ej: Actividad empresarial" className="mt-1" />
                </div>
                <Button type="submit" className="w-full">Registrarme</Button>
              </form>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
