"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  User,
  Shield,
  Loader2,
  CheckCircle,
  AlertCircle,
  Upload,
  Lock,
  KeyRound,
  FileKey,
  Eye,
  EyeOff,
  X,
  Info,
  ArrowRight,
} from "lucide-react";
import { createClient } from "@/lib/supabase";
import { encryptPassword, toBase64 } from "@/lib/crypto";
import { useTenant } from "@/hooks/use-tenant";
import { usePermissions } from "@/hooks/use-permissions";

const REGIMENES: Record<string, string> = {
  RESICO_PF: "Negocio propio / Servicios profesionales",
  RESICO_PF_SUELDOS: "Negocio propio + Sueldo",
  ARRENDAMIENTO: "Renta de propiedades",
  ARRENDAMIENTO_SUELDOS: "Renta de propiedades + Sueldo",
  RESICO_PM: "Persona Moral (RESICO)",
};

interface ProfileData {
  nombre: string | null;
  fecha_nacimiento: string | null;
  email: string;
}

interface BovedaData {
  id: string;
  activa: boolean;
  cer_serie: string | null;
  cer_vigencia_fin: string | null;
  created_at: string;
}

export default function CuentaPage() {
  const { tenant } = useTenant();
  const { canEditProfile, canManageEfirma, rol } = usePermissions();

  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState("");
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [boveda, setBoveda] = useState<BovedaData | null>(null);

  const [nombre, setNombre] = useState("");
  const [fechaNacimiento, setFechaNacimiento] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: "ok" | "error"; text: string } | null>(null);

  const [efirmaZip, setEfirmaZip] = useState<File | null>(null);
  const [efirmaPassword, setEfirmaPassword] = useState("");
  const [showEfirmaPass, setShowEfirmaPass] = useState(false);
  const [savingEfirma, setSavingEfirma] = useState(false);
  const [efirmaMsg, setEfirmaMsg] = useState<{ type: "ok" | "error"; text: string } | null>(null);
  const efirmaInputRef = useRef<HTMLInputElement>(null);

  const [constanciaFile, setConstanciaFile] = useState<File | null>(null);
  const [savingConstancia, setSavingConstancia] = useState(false);
  const [constanciaMsg, setConstanciaMsg] = useState<{ type: "ok" | "error"; text: string } | null>(null);
  const constanciaInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { setLoading(false); return; }
      setUserId(user.id);

      const { data: prof } = await supabase
        .from("user_profiles")
        .select("nombre, fecha_nacimiento, email")
        .eq("id", user.id)
        .single();

      if (prof) {
        setProfile(prof);
        setNombre(prof.nombre ?? "");
        setFechaNacimiento(prof.fecha_nacimiento ?? "");
      }

      if (tenant) {
        if (!prof?.nombre) setNombre(tenant.nombre);

        const { data: bov } = await supabase
          .from("boveda_efirma")
          .select("id, activa, cer_serie, cer_vigencia_fin, created_at")
          .eq("tenant_id", tenant.tenantId)
          .maybeSingle();

        if (bov) setBoveda(bov);
      }

      setLoading(false);
    }
    load();
  }, [tenant]);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!canEditProfile || !tenant) return;
    setProfileMsg(null);

    if (!nombre.trim()) {
      setProfileMsg({ type: "error", text: "Ingresa tu nombre completo." });
      return;
    }

    setSavingProfile(true);

    const supabase = createClient();
    if (!supabase) { setSavingProfile(false); return; }

    const profileUpdate: Record<string, unknown> = { nombre: nombre.trim() };
    if (fechaNacimiento) profileUpdate.fecha_nacimiento = fechaNacimiento;
    await supabase.from("user_profiles").update(profileUpdate).eq("id", userId);

    setSavingProfile(false);
    setProfileMsg({ type: "ok", text: "Información guardada." });
  }

  async function handleUploadConstancia() {
    if (!constanciaFile || !tenant || !canEditProfile) return;
    setSavingConstancia(true);
    setConstanciaMsg(null);

    const supabase = createClient();
    if (!supabase) { setSavingConstancia(false); return; }

    const path = `${tenant.tenantId}/constancia_situacion_fiscal/${constanciaFile.name}`;
    const { error: uploadErr } = await supabase.storage
      .from("documentos")
      .upload(path, constanciaFile, { upsert: true });

    if (uploadErr) {
      setSavingConstancia(false);
      setConstanciaMsg({ type: "error", text: uploadErr.message });
      return;
    }

    await supabase.from("documentos").insert({
      tenant_id: tenant.tenantId,
      nombre_archivo: constanciaFile.name,
      tipo: "constancia_situacion_fiscal",
      estado: "recibido",
      storage_path: path,
      tamano_bytes: constanciaFile.size,
    });

    setSavingConstancia(false);
    setConstanciaFile(null);
    setConstanciaMsg({ type: "ok", text: "Constancia subida correctamente. El régimen se actualizará tras procesarla." });
  }

  async function handleUploadEfirma(e: React.FormEvent) {
    e.preventDefault();
    if (!canManageEfirma) return;
    setEfirmaMsg(null);

    if (!efirmaZip) {
      setEfirmaMsg({ type: "error", text: "Selecciona el archivo ZIP de tu e.firma." });
      return;
    }
    if (!efirmaPassword) {
      setEfirmaMsg({ type: "error", text: "Ingresa la contraseña de tu e.firma." });
      return;
    }
    if (!tenant) {
      setEfirmaMsg({ type: "error", text: "Completa tu información fiscal primero." });
      return;
    }

    setSavingEfirma(true);

    const supabase = createClient();
    if (!supabase) { setSavingEfirma(false); return; }

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) { setSavingEfirma(false); return; }

    const cerPath = `${tenant.tenantId}/efirma/certificado.cer`;
    const keyPath = `${tenant.tenantId}/efirma/llave_privada.key`;

    const { error: uploadErr } = await supabase.storage
      .from("documentos")
      .upload(
        `${tenant.tenantId}/efirma/${efirmaZip.name}`,
        efirmaZip,
        { upsert: true }
      );

    if (uploadErr) {
      setSavingEfirma(false);
      setEfirmaMsg({ type: "error", text: uploadErr.message });
      return;
    }

    let encryptedPassword: Uint8Array;
    let encryptedDataKey: Uint8Array;
    try {
      const result = await encryptPassword(efirmaPassword, user.id);
      encryptedPassword = result.encryptedPassword;
      encryptedDataKey = result.encryptedDataKey;
    } catch {
      setSavingEfirma(false);
      setEfirmaMsg({ type: "error", text: "Error al cifrar la contraseña." });
      return;
    }

    const bovedaPayload = {
      tenant_id: tenant.tenantId,
      cer_storage_path: cerPath,
      key_storage_path: keyPath,
      password_cifrada: toBase64(encryptedPassword),
      data_key_cifrada: toBase64(encryptedDataKey),
      activa: true,
    };

    if (boveda) {
      const { error } = await supabase
        .from("boveda_efirma")
        .update(bovedaPayload)
        .eq("id", boveda.id);
      if (error) {
        setSavingEfirma(false);
        setEfirmaMsg({ type: "error", text: error.message });
        return;
      }
    } else {
      const { data: newBov, error } = await supabase
        .from("boveda_efirma")
        .insert(bovedaPayload)
        .select("id, activa, cer_serie, cer_vigencia_fin, created_at")
        .single();
      if (error) {
        setSavingEfirma(false);
        setEfirmaMsg({ type: "error", text: error.message });
        return;
      }
      setBoveda(newBov);
    }

    await supabase.from("boveda_bitacora").insert({
      tenant_id: tenant.tenantId,
      boveda_id: boveda?.id ?? "",
      accion: "carga_efirma",
      proceso_solicitante: "cuenta/efirma",
      finalidad: "Carga inicial de e.firma por el usuario",
    });

    setSavingEfirma(false);
    setEfirmaPassword("");
    setEfirmaZip(null);
    setEfirmaMsg({ type: "ok", text: "e.firma almacenada de forma segura." });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="animate-fade-in-up">
        <h1 className="font-heading text-2xl font-bold">Mi cuenta</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Tu información fiscal y credenciales de seguridad.
        </p>
      </div>

      <div className="mt-6 space-y-6 max-w-2xl">
        <Card className="animate-fade-in-up stagger-1">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <User className="h-5 w-5" /> Información fiscal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <Label htmlFor="c-nombre">Nombre completo o razón social</Label>
                <Input
                  id="c-nombre"
                  placeholder="Juan Pérez López"
                  className="mt-1"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  disabled={savingProfile || !canEditProfile}
                />
              </div>

              {tenant && (
                <>
                  <div>
                    <Label>RFC</Label>
                    <Input
                      value={tenant.rfc}
                      disabled
                      className="mt-1 uppercase font-mono"
                    />
                    <p className="mt-1 text-xs text-muted-foreground">
                      El RFC se deriva de la constancia de situación fiscal y no se puede editar manualmente.
                    </p>
                  </div>

                  <div>
                    <Label>Régimen fiscal</Label>
                    <div className="mt-1">
                      <Badge>{REGIMENES[tenant.regimen] ?? tenant.regimen}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      El régimen se detecta automáticamente de tu constancia. Para actualizarlo, sube una constancia nueva.
                    </p>
                  </div>
                </>
              )}

              <div>
                <Label htmlFor="c-fecha">Fecha de nacimiento</Label>
                <Input
                  id="c-fecha"
                  type="date"
                  className="mt-1"
                  value={fechaNacimiento}
                  onChange={(e) => setFechaNacimiento(e.target.value)}
                  disabled={savingProfile || !canEditProfile}
                />
              </div>

              <Separator />

              <div>
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Constancia de Situación Fiscal</Label>
                  <Link href="/dashboard/documentos" className="text-xs text-[var(--color-azul)] hover:underline flex items-center gap-1">
                    Ver en Documentos <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
                {canEditProfile ? (
                  <div
                    className={`mt-2 rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
                      constanciaFile
                        ? "border-green-300 bg-green-50"
                        : "border-muted-foreground/25 hover:border-[var(--color-azul)]/50"
                    }`}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      const f = e.dataTransfer.files[0];
                      if (f?.type === "application/pdf") setConstanciaFile(f);
                      else setConstanciaMsg({ type: "error", text: "Solo se aceptan archivos PDF." });
                    }}
                  >
                    {constanciaFile ? (
                      <div className="flex items-center justify-center gap-3">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium">{constanciaFile.name}</span>
                        <button type="button" onClick={() => setConstanciaFile(null)} className="p-1 rounded hover:bg-muted">
                          <X className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </div>
                    ) : (
                      <div>
                        <Upload className="mx-auto h-6 w-6 text-muted-foreground" />
                        <p className="mt-1 text-sm text-muted-foreground">
                          Arrastra tu PDF o{" "}
                          <button type="button" onClick={() => constanciaInputRef.current?.click()} className="text-[var(--color-azul)] underline">
                            selecciona
                          </button>
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Solo archivos PDF — Máximo 10 MB
                        </p>
                        <input
                          ref={constanciaInputRef}
                          type="file"
                          accept=".pdf"
                          className="hidden"
                          onChange={(e) => { if (e.target.files?.[0]) setConstanciaFile(e.target.files[0]); }}
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 rounded-lg border-2 border-dashed border-muted-foreground/15 bg-muted/30 p-4 text-center">
                    <Upload className="mx-auto h-6 w-6 text-muted-foreground/40" />
                    <p className="mt-1 text-sm text-muted-foreground">
                      Tu rol de lectura no permite subir constancias.
                    </p>
                  </div>
                )}
                {constanciaFile && canEditProfile && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-2 gap-1.5"
                    onClick={handleUploadConstancia}
                    disabled={savingConstancia}
                  >
                    {savingConstancia ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                    Subir constancia
                  </Button>
                )}
                {constanciaMsg && (
                  <div className={`mt-2 flex items-center gap-1.5 text-sm ${constanciaMsg.type === "ok" ? "text-green-600" : "text-red-600"}`}>
                    {constanciaMsg.type === "ok" ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                    {constanciaMsg.text}
                  </div>
                )}
              </div>

              {profileMsg && (
                <div className={`flex items-center gap-1.5 text-sm ${profileMsg.type === "ok" ? "text-green-600" : "text-red-600"}`}>
                  {profileMsg.type === "ok" ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  {profileMsg.text}
                </div>
              )}

              {canEditProfile ? (
                <Button type="submit" disabled={savingProfile} className="gap-1.5">
                  {savingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  Guardar cambios
                </Button>
              ) : (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span tabIndex={0}>
                      <Button type="button" disabled className="gap-1.5">
                        Guardar cambios
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    Solo el propietario o contador puede editar la información fiscal.
                  </TooltipContent>
                </Tooltip>
              )}
            </form>
          </CardContent>
        </Card>

        <Card className="animate-fade-in-up stagger-2">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <FileKey className="h-5 w-5" /> e.firma (FIEL)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border bg-blue-50/50 p-3 mb-4">
              <div className="flex gap-2">
                <Shield className="h-5 w-5 text-[var(--color-azul)] shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-foreground">Protocolos de seguridad</p>
                  <ul className="mt-1 space-y-0.5 text-muted-foreground text-xs">
                    <li className="flex items-start gap-1.5">
                      <Lock className="h-3 w-3 mt-0.5 shrink-0" />
                      Contraseña cifrada con AES-256-GCM + PBKDF2 (310,000 iteraciones)
                    </li>
                    <li className="flex items-start gap-1.5">
                      <Lock className="h-3 w-3 mt-0.5 shrink-0" />
                      Archivos almacenados con cifrado en reposo en Supabase Storage
                    </li>
                    <li className="flex items-start gap-1.5">
                      <Lock className="h-3 w-3 mt-0.5 shrink-0" />
                      Acceso restringido por políticas RLS a nivel de tenant
                    </li>
                    <li className="flex items-start gap-1.5">
                      <Lock className="h-3 w-3 mt-0.5 shrink-0" />
                      Bitácora de accesos registrada en cada operación
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {boveda ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                      <KeyRound className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">e.firma activa</p>
                      <p className="text-xs text-muted-foreground">
                        Cargada el {new Date(boveda.created_at).toLocaleDateString("es-MX")}
                        {boveda.cer_serie && ` · Serie: ${boveda.cer_serie}`}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-green-600 border-green-300">
                    Activa
                  </Badge>
                </div>
                {canManageEfirma && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Info className="h-3 w-3" />
                    Para reemplazar tu e.firma, sube un nuevo archivo ZIP.
                  </p>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2 rounded-lg border p-3 mb-4">
                <AlertCircle className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-muted-foreground">
                  No has cargado tu e.firma. Es necesaria para firmar declaraciones.
                </p>
              </div>
            )}

            {canManageEfirma ? (
              <>
                <Separator className="my-4" />
                <form onSubmit={handleUploadEfirma} className="space-y-4">
                  <div>
                    <Label className="text-sm">{boveda ? "Reemplazar" : "Cargar"} e.firma (archivo ZIP)</Label>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      El ZIP debe contener tus archivos .cer y .key
                    </p>
                    <div
                      className={`mt-2 rounded-lg border-2 border-dashed p-4 text-center transition-colors ${
                        efirmaZip
                          ? "border-green-300 bg-green-50"
                          : "border-muted-foreground/25 hover:border-[var(--color-azul)]/50"
                      }`}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const f = e.dataTransfer.files[0];
                        if (f && (f.name.endsWith(".zip") || f.type === "application/zip")) {
                          setEfirmaZip(f);
                        } else {
                          setEfirmaMsg({ type: "error", text: "Solo se aceptan archivos ZIP." });
                        }
                      }}
                    >
                      {efirmaZip ? (
                        <div className="flex items-center justify-center gap-3">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <div className="text-left">
                            <p className="text-sm font-medium">{efirmaZip.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {(efirmaZip.size / 1024).toFixed(0)} KB
                            </p>
                          </div>
                          <button type="button" onClick={() => setEfirmaZip(null)} className="ml-2 p-1 rounded hover:bg-muted">
                            <X className="h-4 w-4 text-muted-foreground" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <FileKey className="mx-auto h-8 w-8 text-muted-foreground" />
                          <p className="mt-2 text-sm font-medium">
                            Arrastra tu archivo ZIP aquí
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            o{" "}
                            <button
                              type="button"
                              onClick={() => efirmaInputRef.current?.click()}
                              className="text-[var(--color-azul)] underline"
                            >
                              selecciona un archivo
                            </button>
                          </p>
                          <input
                            ref={efirmaInputRef}
                            type="file"
                            accept=".zip"
                            className="hidden"
                            onChange={(e) => { if (e.target.files?.[0]) setEfirmaZip(e.target.files[0]); }}
                          />
                        </>
                      )}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="efirma-pass">Contraseña de la e.firma</Label>
                    <div className="relative mt-1">
                      <Input
                        id="efirma-pass"
                        type={showEfirmaPass ? "text" : "password"}
                        placeholder="••••••••"
                        value={efirmaPassword}
                        onChange={(e) => setEfirmaPassword(e.target.value)}
                        disabled={savingEfirma}
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowEfirmaPass((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        tabIndex={-1}
                      >
                        {showEfirmaPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Tu contraseña se cifra localmente antes de enviarla. Nunca se almacena en texto plano.
                    </p>
                  </div>

                  {efirmaMsg && (
                    <div className={`flex items-center gap-1.5 text-sm ${efirmaMsg.type === "ok" ? "text-green-600" : "text-red-600"}`}>
                      {efirmaMsg.type === "ok" ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                      {efirmaMsg.text}
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={savingEfirma || !efirmaZip || !efirmaPassword || !tenant}
                    className="gap-1.5"
                  >
                    {savingEfirma ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Cifrando y guardando...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4" />
                        {boveda ? "Reemplazar e.firma" : "Guardar e.firma de forma segura"}
                      </>
                    )}
                  </Button>
                </form>
              </>
            ) : (
              <>
                <Separator className="my-4" />
                <div className="rounded-lg border bg-muted/30 p-4 text-center">
                  <p className="text-sm text-muted-foreground">
                    {rol === "contador"
                      ? "Solo el propietario puede gestionar la e.firma."
                      : "Tu rol de lectura no permite gestionar la e.firma."}
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
