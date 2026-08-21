"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { createClient } from "@/lib/supabase";
import {
  ClipboardList,
  Upload,
  Loader2,
  ArrowRight,
  Clock,
  X,
  CheckCircle,
  User,
  Building2,
  Briefcase,
  Home,
  Wallet,
} from "lucide-react";

type TipoPersona = "fisica" | "moral" | "";

function derivarRegimen(
  tipoPersona: TipoPersona,
  actividadPrincipal: string,
  tieneSueldo: boolean,
): string {
  if (tipoPersona === "moral") return "RESICO_PM";
  if (actividadPrincipal === "arrendamiento") {
    return tieneSueldo ? "ARRENDAMIENTO_SUELDOS" : "ARRENDAMIENTO";
  }
  if (actividadPrincipal === "resico") {
    return tieneSueldo ? "RESICO_PF_SUELDOS" : "RESICO_PF";
  }
  return "";
}

export function IntroQuestionnaire({ onComplete }: { onComplete?: () => void }) {
  const [nombre, setNombre] = useState("");
  const [rfc, setRfc] = useState("");
  const [tipoPersona, setTipoPersona] = useState<TipoPersona>("");
  const [actividadPrincipal, setActividadPrincipal] = useState("");
  const [tieneSueldo, setTieneSueldo] = useState(false);
  const [fechaNacimiento, setFechaNacimiento] = useState("");
  const [constanciaFile, setConstanciaFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractionDone, setExtractionDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tipoPersonaManual, setTipoPersonaManual] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (tipoPersonaManual) return;
    const clean = rfc.toUpperCase().replace(/\s/g, "");
    if (clean.length === 13 && tipoPersona !== "fisica") setTipoPersona("fisica");
    else if (clean.length === 12 && tipoPersona !== "moral") setTipoPersona("moral");
  }, [rfc, tipoPersona, tipoPersonaManual]);

  function validateRfc(value: string): boolean {
    const clean = value.toUpperCase().replace(/\s/g, "");
    return (
      (clean.length === 12 || clean.length === 13) &&
      /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/.test(clean)
    );
  }

  async function extractFromPdf(file: File) {
    setExtracting(true);
    setExtractionDone(false);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/extract-constancia", {
        method: "POST",
        body: formData,
      });

      const text = await res.text();
      if (!text) {
        setError("No se recibió respuesta del servidor. Intenta de nuevo.");
        return;
      }

      let datos;
      try {
        datos = JSON.parse(text);
      } catch {
        setError("Respuesta inválida del servidor. Intenta de nuevo.");
        return;
      }

      if (!res.ok || !datos.valido) {
        setError(datos.error || "No se pudo extraer datos del PDF");
        return;
      }

      if (datos.rfc && !rfc) setRfc(datos.rfc);
      if (datos.nombre && !nombre) setNombre(datos.nombre);
      if (datos.tipoPersona && !tipoPersona) setTipoPersona(datos.tipoPersona);

      if (datos.regimen && !actividadPrincipal) {
        const r = datos.regimen as string;
        if (r.startsWith("ARRENDAMIENTO")) {
          setActividadPrincipal("arrendamiento");
          if (r.includes("SUELDOS")) setTieneSueldo(true);
        } else if (r.startsWith("RESICO_PF")) {
          setActividadPrincipal("resico");
          if (r.includes("SUELDOS")) setTieneSueldo(true);
        }
      }

      setExtractionDone(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? `Error al leer la constancia: ${err.message}`
          : "No se pudo leer la constancia. Puedes llenar los datos manualmente.",
      );
    } finally {
      setExtracting(false);
    }
  }

  async function handleFileAccepted(file: File) {
    setConstanciaFile(file);
    await extractFromPdf(file);
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
      setError("Selecciona si eres persona física o moral.");
      return;
    }

    const regimen = derivarRegimen(tipoPersona, actividadPrincipal, tieneSueldo);
    if (!regimen) {
      setError("Selecciona tu actividad principal.");
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

    const { data: tenantId, error: rpcError } = await supabase.rpc(
      "crear_tenant_con_membership",
      {
        p_rfc: cleanRfc,
        p_nombre: nombre.trim(),
        p_tipo_persona: tipoPersona,
        p_regimen: regimen,
      },
    );

    if (rpcError || !tenantId) {
      setSaving(false);
      setError(rpcError?.message || "Error al crear la cuenta");
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
      const path = `${tenantId}/constancia_situacion_fiscal/${constanciaFile.name}`;
      await supabase.storage.from("documentos").upload(path, constanciaFile);
      await supabase.from("documentos").insert({
        tenant_id: tenantId,
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
      handleFileAccepted(file);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      handleFileAccepted(file);
    }
  }

  function handleRemoveFile() {
    setConstanciaFile(null);
    setExtractionDone(false);
    setTipoPersonaManual(false);
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
            Necesitamos algunos datos fiscales para preparar tus declaraciones.
          </p>
        </div>

        {/* Constancia upload — optional */}
        <div
          className={`rounded-lg border-2 border-dashed p-3 text-center transition-colors ${
            constanciaFile
              ? "border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950/30"
              : "border-muted-foreground/25 hover:border-[var(--color-azul)]/50"
          }`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
        >
          {extracting ? (
            <div className="flex items-center justify-center gap-3 py-1">
              <Loader2 className="h-5 w-5 animate-spin text-[var(--color-azul)]" />
              <p className="text-sm font-medium text-[var(--color-azul)]">
                Leyendo constancia...
              </p>
            </div>
          ) : constanciaFile ? (
            <div className="flex items-center justify-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
              <div className="text-left">
                <p className="text-sm font-medium">{constanciaFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(constanciaFile.size / 1024).toFixed(0)} KB
                  {extractionDone && " — datos extraídos"}
                </p>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="ml-2 p-1 rounded hover:bg-muted"
              >
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          ) : (
            <div className="py-1">
              <p className="text-sm text-muted-foreground">
                <Upload className="inline h-4 w-4 mr-1 -mt-0.5" />
                ¿Tienes tu Constancia de Situación Fiscal?{" "}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-[var(--color-azul)] underline"
                >
                  Súbela aquí
                </button>{" "}
                para llenar todo automáticamente.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>
          )}
        </div>

        <div className="my-5 flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">
            {extractionDone ? "Verifica los datos" : "Tus datos fiscales"}
          </span>
          <Separator className="flex-1" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Nombre */}
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

          {/* RFC */}
          <div>
            <Label htmlFor="q-rfc">RFC</Label>
            <Input
              id="q-rfc"
              placeholder="XAXX010101000"
              className="mt-1 uppercase font-mono"
              maxLength={13}
              value={rfc}
              onChange={(e) => setRfc(e.target.value.toUpperCase())}
              disabled={saving}
            />
            {rfc.length >= 12 && tipoPersona && (
              <p className="mt-1 text-xs text-muted-foreground">
                Detectado como{" "}
                <span className="font-medium">
                  {tipoPersona === "fisica" ? "Persona Física" : "Persona Moral"}
                </span>
              </p>
            )}
          </div>

          {/* Tipo de persona */}
          <div>
            <Label className="mb-2 block">¿Eres persona física o moral?</Label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => {
                  setTipoPersona("fisica");
                  setTipoPersonaManual(true);
                  if (actividadPrincipal === "") setActividadPrincipal("");
                }}
                disabled={saving}
                className={`flex items-center gap-3 rounded-lg border-2 p-3 text-left transition-colors ${
                  tipoPersona === "fisica"
                    ? "border-[var(--color-azul)] bg-[var(--color-primary-light)]"
                    : "border-muted hover:border-muted-foreground/50"
                }`}
              >
                <User className={`h-5 w-5 shrink-0 ${tipoPersona === "fisica" ? "text-[var(--color-azul)]" : "text-muted-foreground"}`} />
                <div>
                  <p className="text-sm font-medium">Persona Física</p>
                  <p className="text-xs text-muted-foreground">Individuo</p>
                </div>
              </button>
              <button
                type="button"
                onClick={() => {
                  setTipoPersona("moral");
                  setTipoPersonaManual(true);
                  setActividadPrincipal("");
                  setTieneSueldo(false);
                }}
                disabled={saving}
                className={`flex items-center gap-3 rounded-lg border-2 p-3 text-left transition-colors ${
                  tipoPersona === "moral"
                    ? "border-[var(--color-azul)] bg-[var(--color-primary-light)]"
                    : "border-muted hover:border-muted-foreground/50"
                }`}
              >
                <Building2 className={`h-5 w-5 shrink-0 ${tipoPersona === "moral" ? "text-[var(--color-azul)]" : "text-muted-foreground"}`} />
                <div>
                  <p className="text-sm font-medium">Persona Moral</p>
                  <p className="text-xs text-muted-foreground">Empresa</p>
                </div>
              </button>
            </div>
          </div>

          {/* Actividad principal — solo persona física */}
          {tipoPersona === "fisica" && (
            <div>
              <Label className="mb-2 block">¿Cuál es tu actividad principal?</Label>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setActividadPrincipal("resico")}
                  disabled={saving}
                  className={`flex w-full items-center gap-3 rounded-lg border-2 p-3 text-left transition-colors ${
                    actividadPrincipal === "resico"
                      ? "border-[var(--color-azul)] bg-[var(--color-primary-light)]"
                      : "border-muted hover:border-muted-foreground/50"
                  }`}
                >
                  <Briefcase className={`h-5 w-5 shrink-0 ${actividadPrincipal === "resico" ? "text-[var(--color-azul)]" : "text-muted-foreground"}`} />
                  <div>
                    <p className="text-sm font-medium">Negocio propio o servicios profesionales</p>
                    <p className="text-xs text-muted-foreground">
                      Facturas por tu trabajo, honorarios o ventas
                    </p>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setActividadPrincipal("arrendamiento")}
                  disabled={saving}
                  className={`flex w-full items-center gap-3 rounded-lg border-2 p-3 text-left transition-colors ${
                    actividadPrincipal === "arrendamiento"
                      ? "border-[var(--color-azul)] bg-[var(--color-primary-light)]"
                      : "border-muted hover:border-muted-foreground/50"
                  }`}
                >
                  <Home className={`h-5 w-5 shrink-0 ${actividadPrincipal === "arrendamiento" ? "text-[var(--color-azul)]" : "text-muted-foreground"}`} />
                  <div>
                    <p className="text-sm font-medium">Rento propiedades</p>
                    <p className="text-xs text-muted-foreground">
                      Recibo ingresos por renta de inmuebles
                    </p>
                  </div>
                </button>
              </div>
            </div>
          )}

          {/* Persona moral — info */}
          {tipoPersona === "moral" && (
            <div className="rounded-lg border bg-muted/50 p-3">
              <p className="text-sm text-muted-foreground">
                <Building2 className="inline h-4 w-4 mr-1 -mt-0.5" />
                Se configurará con el <span className="font-medium">Régimen Simplificado de Confianza</span> para personas morales.
              </p>
            </div>
          )}

          {/* ¿También recibes sueldo? — solo persona física con actividad seleccionada */}
          {tipoPersona === "fisica" && actividadPrincipal && (
            <label
              className={`flex items-center gap-3 rounded-lg border-2 p-3 cursor-pointer transition-colors ${
                tieneSueldo
                  ? "border-[var(--color-azul)] bg-[var(--color-primary-light)]"
                  : "border-muted hover:border-muted-foreground/50"
              }`}
            >
              <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors ${
                tieneSueldo
                  ? "border-[var(--color-azul)] bg-[var(--color-azul)]"
                  : "border-muted-foreground/50"
              }`}>
                {tieneSueldo && <CheckCircle className="h-3.5 w-3.5 text-white" />}
              </div>
              <Wallet className={`h-5 w-5 shrink-0 ${tieneSueldo ? "text-[var(--color-azul)]" : "text-muted-foreground"}`} />
              <div>
                <p className="text-sm font-medium">También recibo un sueldo</p>
                <p className="text-xs text-muted-foreground">
                  Soy empleado y recibo nómina además de mi actividad
                </p>
              </div>
              <input
                type="checkbox"
                checked={tieneSueldo}
                onChange={(e) => setTieneSueldo(e.target.checked)}
                className="sr-only"
                disabled={saving}
              />
            </label>
          )}

          {/* Fecha de nacimiento — solo persona física */}
          {tipoPersona === "fisica" && (
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
          )}

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
            <Button
              type="submit"
              size="sm"
              className="gap-1.5"
              disabled={saving || extracting}
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  Continuar
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
