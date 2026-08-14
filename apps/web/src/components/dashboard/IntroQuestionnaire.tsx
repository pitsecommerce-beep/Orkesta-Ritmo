"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { createClient } from "@/lib/supabase";
import {
  ClipboardList,
  Upload,
  FileText,
  Loader2,
  ArrowRight,
  Clock,
  X,
  CheckCircle,
} from "lucide-react";

const REGIMENES = [
  { value: "RESICO_PF", label: "RESICO Persona Física" },
  { value: "RESICO_PF_SUELDOS", label: "RESICO PF con Sueldos" },
  { value: "ARRENDAMIENTO", label: "Arrendamiento" },
  { value: "ARRENDAMIENTO_SUELDOS", label: "Arrendamiento con Sueldos" },
] as const;

const TIPO_PERSONA = [
  { value: "fisica", label: "Persona Física" },
  { value: "moral", label: "Persona Moral" },
] as const;

export function IntroQuestionnaire({ onComplete }: { onComplete?: () => void }) {
  const [nombre, setNombre] = useState("");
  const [rfc, setRfc] = useState("");
  const [tipoPersona, setTipoPersona] = useState("");
  const [regimen, setRegimen] = useState("");
  const [fechaNacimiento, setFechaNacimiento] = useState("");
  const [constanciaFile, setConstanciaFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function validateRfc(value: string): boolean {
    const clean = value.toUpperCase().replace(/\s/g, "");
    return (clean.length === 12 || clean.length === 13) && /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/.test(clean);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!nombre.trim()) {
      setError("Ingresa tu nombre completo.");
      return;
    }

    const cleanRfc = rfc.toUpperCase().replace(/\s/g, "");
    if (!validateRfc(cleanRfc)) {
      setError("El RFC no tiene un formato válido (12 o 13 caracteres).");
      return;
    }

    if (!tipoPersona) {
      setError("Selecciona el tipo de persona.");
      return;
    }

    if (!regimen) {
      setError("Selecciona tu régimen fiscal.");
      return;
    }

    setSaving(true);

    const supabase = createClient();
    if (!supabase) {
      setSaving(false);
      return;
    }

    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setSaving(false);
      return;
    }

    const { data: tenant, error: tenantError } = await supabase
      .from("tenants")
      .insert({
        rfc: cleanRfc,
        nombre: nombre.trim(),
        tipo_persona: tipoPersona,
        regimen,
      })
      .select("id")
      .single();

    if (tenantError) {
      setSaving(false);
      setError(tenantError.message);
      return;
    }

    const { error: memberError } = await supabase.from("memberships").insert({
      tenant_id: tenant.id,
      user_id: user.id,
      rol: "propietario",
    });

    if (memberError) {
      setSaving(false);
      setError(memberError.message);
      return;
    }

    const profileUpdate: Record<string, unknown> = {
      nombre: nombre.trim(),
    };
    if (fechaNacimiento) {
      profileUpdate.fecha_nacimiento = fechaNacimiento;
    }
    await supabase.from("user_profiles").update(profileUpdate).eq("id", user.id);

    if (constanciaFile) {
      const path = `${tenant.id}/constancia_situacion_fiscal/${constanciaFile.name}`;
      await supabase.storage.from("documentos").upload(path, constanciaFile);
      await supabase.from("documentos").insert({
        tenant_id: tenant.id,
        nombre_archivo: constanciaFile.name,
        tipo: "constancia_situacion_fiscal",
        estado: "recibido",
        storage_path: path,
        tamano_bytes: constanciaFile.size,
      });
    }

    setSaving(false);
    onComplete?.();
  }

  function handleSkip() {
    onComplete?.();
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      setConstanciaFile(file);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setConstanciaFile(file);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 animate-fade-in" />

      <div className="relative z-10 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto rounded-lg border bg-background p-6 shadow-lg animate-scale-in">
        <button
          onClick={handleSkip}
          className="absolute right-3 top-3 rounded-sm p-1 text-muted-foreground hover:text-foreground transition-opacity"
          aria-label="Cerrar"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-primary-light)]">
            <ClipboardList className="h-6 w-6 text-[var(--color-azul)]" />
          </div>
          <h2 className="mt-4 font-heading text-lg font-bold">
            Comencemos por lo básico
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Necesitamos algunos datos fiscales para configurar tu cuenta.
          </p>
        </div>

        <div
          className={`rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
            constanciaFile
              ? "border-green-300 bg-green-50"
              : "border-muted-foreground/25 hover:border-[var(--color-azul)]/50"
          }`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
        >
          {constanciaFile ? (
            <div className="flex items-center justify-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div className="text-left">
                <p className="text-sm font-medium">{constanciaFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(constanciaFile.size / 1024).toFixed(0)} KB
                </p>
              </div>
              <button
                type="button"
                onClick={() => setConstanciaFile(null)}
                className="ml-2 p-1 rounded hover:bg-muted"
              >
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          ) : (
            <>
              <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium">
                Sube tu Constancia de Situación Fiscal
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Arrastra tu PDF aquí o{" "}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-[var(--color-azul)] underline"
                >
                  selecciona un archivo
                </button>
              </p>
              <p className="mt-1 text-xs text-muted-foreground italic">
                Próximamente: llenado automático desde el PDF
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleFileSelect}
              />
            </>
          )}
        </div>

        <div className="my-5 flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">
            Completa manualmente
          </span>
          <Separator className="flex-1" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="q-nombre">Nombre completo o razón social</Label>
            <Input
              id="q-nombre"
              placeholder="Juan Pérez López"
              className="mt-1"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={saving}
            />
          </div>

          <div>
            <Label htmlFor="q-rfc">RFC</Label>
            <Input
              id="q-rfc"
              placeholder="XAXX010101000"
              className="mt-1 uppercase"
              maxLength={13}
              value={rfc}
              onChange={(e) => setRfc(e.target.value.toUpperCase())}
              disabled={saving}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Tipo de persona</Label>
              <Select
                value={tipoPersona}
                onValueChange={setTipoPersona}
                disabled={saving}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecciona" />
                </SelectTrigger>
                <SelectContent>
                  {TIPO_PERSONA.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Régimen fiscal</Label>
              <Select
                value={regimen}
                onValueChange={setRegimen}
                disabled={saving}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Selecciona" />
                </SelectTrigger>
                <SelectContent>
                  {REGIMENES.map((r) => (
                    <SelectItem key={r.value} value={r.value}>
                      {r.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="q-fecha">Fecha de nacimiento (opcional)</Label>
            <Input
              id="q-fecha"
              type="date"
              className="mt-1"
              value={fechaNacimiento}
              onChange={(e) => setFechaNacimiento(e.target.value)}
              disabled={saving}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex items-center justify-between pt-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="gap-1.5 text-muted-foreground"
            >
              <Clock className="h-3.5 w-3.5" />
              Dejar para después
            </Button>
            <Button type="submit" size="sm" className="gap-1.5" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  Guardar
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
