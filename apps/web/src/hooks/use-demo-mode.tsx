"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface DemoModeContextType {
  demoMode: boolean;
  setDemoMode: (v: boolean) => void;
}

const DemoModeContext = createContext<DemoModeContextType>({
  demoMode: false,
  setDemoMode: () => {},
});

export function DemoModeProvider({ children }: { children: ReactNode }) {
  const [demoMode, setDemoModeState] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("orkesta-demo-mode");
    if (stored === "true") setDemoModeState(true);
  }, []);

  function setDemoMode(v: boolean) {
    setDemoModeState(v);
    localStorage.setItem("orkesta-demo-mode", String(v));
  }

  return (
    <DemoModeContext.Provider value={{ demoMode, setDemoMode }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  return useContext(DemoModeContext);
}
