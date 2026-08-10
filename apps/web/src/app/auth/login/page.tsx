"use client";

import { useState } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-16">
      <Link href="/">
        <Logo type="full" className="mb-8" />
      </Link>

      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="font-heading text-xl">
            {sent ? "Revisa tu correo" : "Iniciar sesión"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="text-center">
              <Mail className="mx-auto h-10 w-10 text-[var(--color-azul)]" />
              <p className="mt-4 text-sm text-muted-foreground">
                Enviamos un enlace mágico a <strong className="text-foreground">{email}</strong>.
                Haz clic en el enlace para acceder.
              </p>
              <Button variant="link" className="mt-4" onClick={() => setSent(false)}>
                Usar otro correo
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">Correo electrónico</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  placeholder="tu@correo.com"
                  className="mt-1"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full gap-2">
                Enviar enlace mágico <ArrowRight className="h-4 w-4" />
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                Sin contraseñas. Te enviamos un enlace seguro a tu correo.
              </p>
            </form>
          )}
        </CardContent>
      </Card>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        Al continuar, aceptas nuestros{" "}
        <Link href="/terminos" className="underline">Términos</Link> y{" "}
        <Link href="/privacidad" className="underline">Aviso de Privacidad</Link>.
      </p>
    </div>
  );
}
