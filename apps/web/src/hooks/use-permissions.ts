"use client";

import { useMemo } from "react";
import { useTenant, type RolUsuario } from "@/hooks/use-tenant";

export interface Permissions {
  canUpload: boolean;
  canDelete: boolean;
  canCalculate: boolean;
  canInvite: boolean;
  canEditProfile: boolean;
  canManageEfirma: boolean;
  rol: RolUsuario | null;
}

function permissionsForRole(rol: RolUsuario | null): Permissions {
  if (rol === "propietario" || rol === "contador") {
    return {
      canUpload: true,
      canDelete: rol === "propietario",
      canCalculate: true,
      canInvite: true,
      canEditProfile: true,
      canManageEfirma: rol === "propietario",
      rol,
    };
  }

  return {
    canUpload: false,
    canDelete: false,
    canCalculate: false,
    canInvite: false,
    canEditProfile: false,
    canManageEfirma: false,
    rol: rol ?? null,
  };
}

export function usePermissions(): Permissions {
  const { tenant } = useTenant();
  return useMemo(() => permissionsForRole(tenant?.rol ?? null), [tenant?.rol]);
}
