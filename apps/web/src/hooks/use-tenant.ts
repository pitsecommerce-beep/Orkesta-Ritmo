"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase";

interface TenantInfo {
  tenantId: string;
  rfc: string;
  nombre: string;
  regimen: string;
}

export function useTenant() {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      if (!supabase) { setLoading(false); return; }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { setLoading(false); return; }

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
          setTenant({
            tenantId: t.id,
            rfc: t.rfc,
            nombre: t.nombre,
            regimen: t.regimen,
          });
        }
      }

      setLoading(false);
    }
    load();
  }, []);

  return { tenant, loading };
}
