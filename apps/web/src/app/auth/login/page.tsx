"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Loader2, CloudOff, Eye, EyeOff, Mail, KeyRound, CheckCircle } from "lucide-react";
import { createClient } from "@/lib/supabase";
import { isSupabaseConfigured } from "@/lib/env";

const supabaseReady = isSupabaseConfigured();

type AuthMode = "login" | "signup" | "magic-link";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const supabase = createClient();
    if (!supabase) {
      return;
    }

    if (mode === "magic-link") {
      if (!email) {
        setError("Ingresa tu correo electronico.");
        return;
      }
      setLoading(true);

      const redirectTo = `${window.location.origin}/auth/callback`;
      const { error: otpError } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: redirectTo },
      });

      setLoading(false);
      if (otpError) {
        setError(otpError.message);
        return;
      }
      setMagicLinkSent(true);
      return;
    }

    if (mode === "signup" && password !== confirmPassword) {
      setError("Las contrasenas no coinciden.");
      return;
    }

    if (password.length < 6) {
      setError("La contrasena debe tener al menos 6 caracteres.");
      return;
    }

    setLoading(true);

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
        } else if (authError.message === "Email not confirmed") {
          setError(
            "Tu correo no ha sido confirmado. Usa el enlace magico para iniciar sesion y confirmar tu cuenta automaticamente."
          );
        } else {
          setError(authError.message);
        }
        return;
      }
      router.push("/dashboard");
    }
  }

  function switchMode(newMode: AuthMode) {
    setMode(newMode);
    setError(null);
    setMagicLinkSent(false);
  }

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-16">
      <Link href="/">
        <Logo type="full" className="mb-8 animate-fade-in" />
      </Link>

      <Card className="w-full max-w-sm animate-scale-in">
        <CardHeader className="text-center">
          <CardTitle className="font-heading text-xl">
            {mode === "login"
              ? "Iniciar sesion"
              : mode === "signup"
                ? "Crear cuenta"
                : "Enlace magico"}
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
          ) : magicLinkSent ? (
            <div className="text-center py-4">
              <CheckCircle className="mx-auto h-10 w-10 text-green-500" />
              <p className="mt-4 text-sm font-medium">
                Revisa tu correo electronico
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Enviamos un enlace de acceso a <strong>{email}</strong>. Haz
                clic en el enlace del correo para iniciar sesion.
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => {
                  setMagicLinkSent(false);
                  setMode("login");
                }}
              >
                Volver al login
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode !== "signup" && (
                <div className="flex rounded-md border overflow-hidden">
                  <button
                    type="button"
                    onClick={() => switchMode("login")}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-sm font-medium transition-colors ${
                      mode === "login"
                        ? "bg-[var(--color-azul)] text-white"
                        : "hover:bg-muted"
                    }`}
                  >
                    <KeyRound className="h-3.5 w-3.5" />
                    Contrasena
                  </button>
                  <button
                    type="button"
                    onClick={() => switchMode("magic-link")}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-sm font-medium transition-colors ${
                      mode === "magic-link"
                        ? "bg-[var(--color-azul)] text-white"
                        : "hover:bg-muted"
                    }`}
                  >
                    <Mail className="h-3.5 w-3.5" />
                    Enlace magico
                  </button>
                </div>
              )}

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

              {mode !== "magic-link" && (
                <div>
                  <Label htmlFor="password">Contrasena</Label>
                  <div className="relative mt-1">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="******"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loading}
                      minLength={6}
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      tabIndex={-1}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {mode === "signup" && (
                <div>
                  <Label htmlFor="confirmPassword">Confirmar contrasena</Label>
                  <div className="relative mt-1">
                    <Input
                      id="confirmPassword"
                      type={showConfirm ? "text" : "password"}
                      required
                      placeholder="******"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={loading}
                      minLength={6}
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      tabIndex={-1}
                    >
                      {showConfirm ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {error && <p className="text-sm text-destructive">{error}</p>}

              {mode === "magic-link" && (
                <p className="text-xs text-muted-foreground">
                  Te enviaremos un enlace de acceso a tu correo. No necesitas
                  contrasena.
                </p>
              )}

              <Button
                type="submit"
                className="w-full gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {mode === "login"
                      ? "Entrando..."
                      : mode === "signup"
                        ? "Creando cuenta..."
                        : "Enviando enlace..."}
                  </>
                ) : (
                  <>
                    {mode === "login"
                      ? "Iniciar sesion"
                      : mode === "signup"
                        ? "Crear cuenta"
                        : "Enviar enlace"}
                    {mode === "magic-link" ? (
                      <Mail className="h-4 w-4" />
                    ) : (
                      <ArrowRight className="h-4 w-4" />
                    )}
                  </>
                )}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                {mode === "signup" ? (
                  <>
                    Ya tienes cuenta?{" "}
                    <button
                      type="button"
                      onClick={() => switchMode("login")}
                      className="text-[var(--color-azul)] underline"
                    >
                      Inicia sesion
                    </button>
                  </>
                ) : (
                  <>
                    No tienes cuenta?{" "}
                    <button
                      type="button"
                      onClick={() => switchMode("signup")}
                      className="text-[var(--color-azul)] underline"
                    >
                      Registrate
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
        <Link href="/terminos" className="underline">
          Terminos
        </Link>{" "}
        y{" "}
        <Link href="/privacidad" className="underline">
          Aviso de Privacidad
        </Link>
        .
      </p>
    </div>
  );
}
