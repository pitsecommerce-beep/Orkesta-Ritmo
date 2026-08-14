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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { createClient } from "@/lib/supabase";
import { Switch } from "@/components/ui/switch";
import { useDemoMode } from "@/hooks/use-demo-mode";
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

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-background animate-slide-in-left">
      <div className="flex h-16 items-center border-b px-4">
        <Link href="/dashboard">
          <Logo type="full" />
        </Link>
      </div>

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
