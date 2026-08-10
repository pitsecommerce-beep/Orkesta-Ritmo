"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Shield, Users, Settings } from "lucide-react";

export default function ConfiguracionPage() {
  return (
    <div className="p-6 lg:p-8">
      <h1 className="font-heading text-2xl font-bold">Configuración</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Administra tu workspace y preferencias.
      </p>

      <div className="mt-6 space-y-6 max-w-2xl">
        {/* Workspace info */}
        <Card>
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Settings className="h-5 w-5" /> Workspace
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>RFC</Label>
              <Input value="XXXX010101AAA" disabled className="mt-1 font-mono" />
            </div>
            <div>
              <Label>Nombre / Razón social</Label>
              <Input value="Contribuyente Demo" className="mt-1" />
            </div>
            <div>
              <Label>Régimen fiscal</Label>
              <div className="mt-1">
                <Badge>RESICO Persona Física</Badge>
              </div>
            </div>
            <div>
              <Label>Ejercicio activo</Label>
              <div className="mt-1">
                <Badge variant="outline">2025</Badge>
              </div>
            </div>
            <Button>Guardar cambios</Button>
          </CardContent>
        </Card>

        {/* Team */}
        <Card>
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Users className="h-5 w-5" /> Equipo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded border p-3">
                <div>
                  <p className="font-medium text-sm">usuario@demo.com</p>
                  <p className="text-xs text-muted-foreground">Tú</p>
                </div>
                <Badge>Propietario</Badge>
              </div>
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
        <Card>
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Shield className="h-5 w-5" /> Seguridad
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Bóveda de e.firma</p>
                <p className="text-xs text-muted-foreground">
                  Almacena tu .cer y .key cifrados con AES-256-GCM
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-sm">Cookies de analítica</p>
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
