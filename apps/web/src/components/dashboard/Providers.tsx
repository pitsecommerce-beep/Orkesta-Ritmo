"use client";

import { DemoModeProvider } from "@/hooks/use-demo-mode";
import { TenantProvider } from "@/hooks/use-tenant";
import type { ReactNode } from "react";

export function DashboardProviders({ children }: { children: ReactNode }) {
  return (
    <DemoModeProvider>
      <TenantProvider>{children}</TenantProvider>
    </DemoModeProvider>
  );
}
