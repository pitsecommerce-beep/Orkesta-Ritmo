"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import {
  Home,
  FileText,
  Calendar,
  Upload,
  Building2,
  MessageSquare,
  Settings,
  LogOut,
  FlaskConical,
  User,
  ChevronsUpDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { useDemoMode } from "@/hooks/use-demo-mode";
import { useTenant } from "@/hooks/use-tenant";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ROL_LABELS: Record<string, string> = {
  propietario: "Propietario",
  contador: "Contador",
  lectura: "Lectura",
};

const ROL_COLORS: Record<string, string> = {
  propietario: "bg-green-100 text-green-700 border-green-200",
  contador: "bg-blue-100 text-blue-700 border-blue-200",
  lectura: "bg-gray-100 text-gray-600 border-gray-200",
};

const NAV_ITEMS = [
  { href: "/dashboard", label: "Inicio", icon: Home },
  { href: "/dashboard/periodos", label: "Periodos", icon: Calendar },
  { href: "/dashboard/documentos", label: "Documentos", icon: Upload },
  { href: "/dashboard/cfdis", label: "CFDIs", icon: FileText },
  { href: "/dashboard/extractos", label: "Extractos", icon: Building2 },
  { href: "/dashboard/chat", label: "Asistente", icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();
  const { demoMode, setDemoMode } = useDemoMode();
  const { tenant, tenants, switchTenant } = useTenant();

  const showTenantSelector = tenants.length > 1;

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-background animate-slide-in-left">
      <div className="flex h-16 items-center border-b px-4">
        <Link href="/dashboard">
          <Logo type="full" />
        </Link>
      </div>

      {showTenantSelector && (
        <div className="border-b px-3 py-3">
          <label className="mb-1 block text-xs font-medium text-muted-foreground">
            Contribuyente activo
          </label>
          <Select
            value={tenant?.tenantId ?? ""}
            onValueChange={switchTenant}
          >
            <SelectTrigger className="h-auto py-1.5 text-left">
              <SelectValue placeholder="Selecciona contribuyente" />
            </SelectTrigger>
            <SelectContent>
              {tenants.map((t) => (
                <SelectItem key={t.tenantId} value={t.tenantId}>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{t.nombre}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {t.rfc}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {tenant && (
        <div className="border-b px-3 py-2">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{tenant.nombre}</p>
              <p className="text-xs text-muted-foreground font-mono">
                {tenant.rfc}
              </p>
            </div>
            <Badge
              variant="outline"
              className={cn(
                "ml-2 shrink-0 text-[10px] capitalize",
                ROL_COLORS[tenant.rol] ?? ROL_COLORS.lectura,
              )}
            >
              {ROL_LABELS[tenant.rol] ?? tenant.rol}
            </Badge>
          </div>
        </div>
      )}

      <nav className="flex-1 space-y-0.5 p-3">
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              data-tour-target={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all",
                active
                  ? "bg-[var(--color-primary-light)] text-[var(--color-azul)]"
                  : "text-muted-foreground hover:bg-[var(--color-primary-light)] hover:text-foreground",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-3 space-y-0.5">
        <div className="flex items-center justify-between rounded-md px-3 py-2">
          <div className="flex items-center gap-3 text-sm font-medium text-muted-foreground">
            <FlaskConical className="h-4 w-4" />
            Demo
          </div>
          <Switch
            checked={demoMode}
            onCheckedChange={setDemoMode}
            aria-label="Modo demo"
          />
        </div>

        <Link
          href="/dashboard/cuenta"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-[var(--color-primary-light)] hover:text-foreground transition-all"
        >
          <User className="h-4 w-4" />
          Mi cuenta
        </Link>

        <Link
          href="/dashboard/configuracion"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-[var(--color-primary-light)] hover:text-foreground transition-all"
        >
          <Settings className="h-4 w-4" />
          Configuración
        </Link>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-[var(--color-primary-light)] hover:text-foreground transition-all">
              <LogOut className="h-4 w-4" />
              Cerrar sesión
            </button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cerrar sesión</AlertDialogTitle>
              <AlertDialogDescription>
                ¿Estás seguro de que quieres cerrar tu sesión?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={async () => {
                  const supabase = createClient();
                  if (supabase) {
                    await supabase.auth.signOut();
                    window.location.href = "/auth/login";
                  }
                }}
              >
                Cerrar sesión
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </aside>
  );
}
