"use client";

import { useState } from "react";
import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, ArrowRight, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    if (!supabase) {
      setError("Supabase no está configurado. Contacta al administrador.");
      setLoading(false);
      return;
    }

    const { error: authError } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    setLoading(false);

    if (authError) {
      setError(authError.message);
      return;
    }

    setSent(true);
  }

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-16">
      <Link href="/">
        <Logo type="full" className="mb-8 animate-fade-in" />
      </Link>

      <Card className="w-full max-w-sm animate-scale-in">
        <CardHeader className="text-center">
          <CardTitle className="font-heading text-xl">
            {sent ? "Revisa tu correo" : "Iniciar sesion"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="text-center">
              <Mail className="mx-auto h-10 w-10 text-[var(--color-azul)]" />
              <p className="mt-4 text-sm text-muted-foreground">
                Enviamos un enlace magico a <strong className="text-foreground">{email}</strong>.
                Haz clic en el enlace para acceder.
              </p>
              <Button variant="link" className="mt-4" onClick={() => setSent(false)}>
                Usar otro correo
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">Correo electronico</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  placeholder="tu@correo.com"
                  className="mt-1"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button type="submit" className="w-full gap-2" disabled={loading}>
                {loading ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Enviando...</>
                ) : (
                  <>Enviar enlace magico <ArrowRight className="h-4 w-4" /></>
                )}
              </Button>
              <p className="text-center text-xs text-muted-foreground">
                Sin contrasenas. Te enviamos un enlace seguro a tu correo.
              </p>
            </form>
          )}
        </CardContent>
      </Card>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        Al continuar, aceptas nuestros{" "}
        <Link href="/terminos" className="underline">Terminos</Link> y{" "}
        <Link href="/privacidad" className="underline">Aviso de Privacidad</Link>.
      </p>
    </div>
  );
}
