"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Shield, Users, Settings, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase";

const REGIMEN_LABELS: Record<string, string> = {
  RESICO_PF: "RESICO Persona Fisica",
  RESICO_PF_SUELDOS: "RESICO PF + Sueldos",
  ARRENDAMIENTO: "Arrendamiento",
  ARRENDAMIENTO_SUELDOS: "Arrendamiento + Sueldos",
  RESICO_PM: "RESICO Persona Moral",
};

interface TenantData {
  id: string;
  rfc: string;
  nombre: string;
  regimen: string;
}

interface MembershipData {
  rol: string;
  user_id: string;
  user_profiles: { email: string } | null;
}

export default function ConfiguracionPage() {
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState("");
  const [tenant, setTenant] = useState<TenantData | null>(null);
  const [members, setMembers] = useState<MembershipData[]>([]);
  const [nombre, setNombre] = useState("");

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { setLoading(false); return; }

      setUserEmail(user.email ?? "");

      const { data: membership } = await supabase
        .from("memberships")
        .select("tenant_id")
        .eq("user_id", user.id)
        .maybeSingle();

      if (membership) {
        const { data: t } = await supabase
          .from("tenants")
          .select("id, rfc, nombre, regimen")
          .eq("id", membership.tenant_id)
          .single();

        if (t) {
          setTenant(t);
          setNombre(t.nombre);
        }

        const { data: m } = await supabase
          .from("memberships")
          .select("rol, user_id, user_profiles(email)")
          .eq("tenant_id", membership.tenant_id);

        if (m) setMembers(m as unknown as MembershipData[]);
      }

      setLoading(false);
    }
    load();
  }, []);

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
        <h1 className="font-heading text-2xl font-bold">Configuracion</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Administra tu workspace y preferencias.
        </p>
      </div>

      <div className="mt-6 space-y-6 max-w-2xl">
        {/* Workspace info */}
        <Card className="animate-fade-in-up stagger-1">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Settings className="h-5 w-5" /> Workspace
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tenant ? (
              <>
                <div>
                  <Label>RFC</Label>
                  <Input value={tenant.rfc} disabled className="mt-1 font-mono" />
                </div>
                <div>
                  <Label>Nombre / Razon social</Label>
                  <Input
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>Regimen fiscal</Label>
                  <div className="mt-1">
                    <Badge>{REGIMEN_LABELS[tenant.regimen] ?? tenant.regimen}</Badge>
                  </div>
                </div>
                <Button
                  onClick={async () => {
                    const supabase = createClient();
                    if (!supabase || !tenant) return;
                    await supabase
                      .from("tenants")
                      .update({ nombre })
                      .eq("id", tenant.id);
                  }}
                >
                  Guardar cambios
                </Button>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Completa el onboarding para configurar tu workspace.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Team */}
        <Card className="animate-fade-in-up stagger-2">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Users className="h-5 w-5" /> Equipo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {members.length > 0 ? (
                members.map((m) => {
                  const email = m.user_profiles?.email ?? "Sin correo";
                  const isMe = email === userEmail;
                  return (
                    <div key={m.user_id} className="flex items-center justify-between rounded border p-3">
                      <div>
                        <p className="font-medium text-sm">{email}</p>
                        {isMe && <p className="text-xs text-muted-foreground">Tu</p>}
                      </div>
                      <Badge className="capitalize">{m.rol}</Badge>
                    </div>
                  );
                })
              ) : (
                <div className="flex items-center justify-between rounded border p-3">
                  <div>
                    <p className="font-medium text-sm">{userEmail}</p>
                    <p className="text-xs text-muted-foreground">Tu</p>
                  </div>
                  <Badge>Propietario</Badge>
                </div>
              )}
            </div>
            <Separator className="my-4" />
            <div>
              <Label>Invitar miembro</Label>
              <div className="mt-1 flex gap-2">
                <Input placeholder="correo@ejemplo.com" className="flex-1" />
                <Button variant="outline">Invitar</Button>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Roles disponibles: propietario, contador, lectura
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card className="animate-fade-in-up stagger-3">
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Shield className="h-5 w-5" /> Seguridad
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Boveda de e.firma</p>
                <p className="text-xs text-muted-foreground">
                  Almacena tu .cer y .key cifrados con AES-256-GCM
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Cookies de analitica</p>
                <p className="text-xs text-muted-foreground">Desactivadas por defecto</p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
