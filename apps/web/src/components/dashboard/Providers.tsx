"use client";

import { DemoModeProvider } from "@/hooks/use-demo-mode";
import type { ReactNode } from "react";

export function DashboardProviders({ children }: { children: ReactNode }) {
  return <DemoModeProvider>{children}</DemoModeProvider>;
}
