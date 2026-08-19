"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { createClient } from "@/lib/supabase";

export type RolUsuario = "propietario" | "contador" | "lectura";

export interface TenantInfo {
  tenantId: string;
  rfc: string;
  nombre: string;
  regimen: string;
  rol: RolUsuario;
}

interface TenantContextType {
  tenant: TenantInfo | null;
  tenants: TenantInfo[];
  loading: boolean;
  switchTenant: (tenantId: string) => void;
}

const TenantContext = createContext<TenantContextType>({
  tenant: null,
  tenants: [],
  loading: true,
  switchTenant: () => {},
});

const STORAGE_KEY = "orkesta-active-tenant";

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenants, setTenants] = useState<TenantInfo[]>([]);
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      if (!supabase) {
        setLoading(false);
        return;
      }

      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) {
        setLoading(false);
        return;
      }

      const { data: memberships } = await supabase
        .from("memberships")
        .select("tenant_id, rol")
        .eq("user_id", user.id);

      if (!memberships || memberships.length === 0) {
        setLoading(false);
        return;
      }

      const tenantIds = memberships.map((m) => m.tenant_id);
      const { data: tenantRows } = await supabase
        .from("tenants")
        .select("id, rfc, nombre, regimen")
        .in("id", tenantIds);

      if (!tenantRows) {
        setLoading(false);
        return;
      }

      const rolMap = new Map(
        memberships.map((m) => [m.tenant_id, m.rol as RolUsuario]),
      );

      const list: TenantInfo[] = tenantRows.map((t) => ({
        tenantId: t.id,
        rfc: t.rfc,
        nombre: t.nombre,
        regimen: t.regimen,
        rol: rolMap.get(t.id) ?? "lectura",
      }));

      setTenants(list);

      const stored = localStorage.getItem(STORAGE_KEY);
      const storedValid = list.find((t) => t.tenantId === stored);
      setActiveTenantId(storedValid ? stored : list[0].tenantId);

      setLoading(false);
    }
    load();
  }, []);

  const switchTenant = useCallback(
    (tenantId: string) => {
      const found = tenants.find((t) => t.tenantId === tenantId);
      if (found) {
        setActiveTenantId(tenantId);
        localStorage.setItem(STORAGE_KEY, tenantId);
      }
    },
    [tenants],
  );

  const tenant = tenants.find((t) => t.tenantId === activeTenantId) ?? null;

  return (
    <TenantContext.Provider value={{ tenant, tenants, loading, switchTenant }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
