"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Loader2, CloudOff } from "lucide-react";
import { createClient } from "@/lib/supabase";
import { isSupabaseConfigured } from "@/lib/env";

const supabaseReady = isSupabaseConfigured();

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (mode === "signup" && password !== confirmPassword) {
      setError("Las contrasenas no coinciden.");
      return;
    }

    if (password.length < 6) {
      setError("La contrasena debe tener al menos 6 caracteres.");
      return;
    }

    setLoading(true);

    const supabase = createClient();
    if (!supabase) {
      setLoading(false);
      return;
    }

    if (mode === "signup") {
      const { error: authError } = await supabase.auth.signUp({
        email,
        password,
      });
      setLoading(false);
      if (authError) {
        setError(authError.message);
        return;
      }
      router.push("/dashboard");
    } else {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      setLoading(false);
      if (authError) {
        if (authError.message === "Invalid login credentials") {
          setError("Correo o contrasena incorrectos.");
        } else {
          setError(authError.message);
        }
        return;
      }
      router.push("/dashboard");
    }
  }

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-16">
      <Link href="/">
        <Logo type="full" className="mb-8 animate-fade-in" />
      </Link>

      <Card className="w-full max-w-sm animate-scale-in">
        <CardHeader className="text-center">
          <CardTitle className="font-heading text-xl">
            {mode === "login" ? "Iniciar sesion" : "Crear cuenta"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!supabaseReady ? (
            <div className="text-center">
              <CloudOff className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-4 text-sm text-muted-foreground">
                Login disponible en produccion.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Las variables de entorno de Supabase se configuran en Railway.
              </p>
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
              <div>
                <Label htmlFor="password">Contrasena</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  placeholder="******"
                  className="mt-1"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  minLength={6}
                />
              </div>
              {mode === "signup" && (
                <div>
                  <Label htmlFor="confirmPassword">Confirmar contrasena</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    required
                    placeholder="******"
                    className="mt-1"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={loading}
                    minLength={6}
                  />
                </div>
              )}
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button type="submit" className="w-full gap-2" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {mode === "login" ? "Entrando..." : "Creando cuenta..."}
                  </>
                ) : (
                  <>
                    {mode === "login" ? "Iniciar sesion" : "Crear cuenta"}
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                {mode === "login" ? (
                  <>
                    No tienes cuenta?{" "}
                    <button
                      type="button"
                      onClick={() => { setMode("signup"); setError(null); }}
                      className="text-[var(--color-azul)] underline"
                    >
                      Registrate
                    </button>
                  </>
                ) : (
                  <>
                    Ya tienes cuenta?{" "}
                    <button
                      type="button"
                      onClick={() => { setMode("login"); setError(null); }}
                      className="text-[var(--color-azul)] underline"
                    >
                      Inicia sesion
                    </button>
                  </>
                )}
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
