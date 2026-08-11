"use client";

import { AlertTriangle, Shield } from "lucide-react";

export function TarifaAlertBanner({ ejercicio = 2026 }: { ejercicio?: number }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--color-warning)]/20 bg-[var(--color-warning-light)] p-4 text-sm">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-warning)]" />
      <div>
        <p className="font-medium text-amber-900 dark:text-amber-200">
          Tarifas {ejercicio} no disponibles
        </p>
        <p className="mt-1 text-amber-800/80 dark:text-amber-300/80">
          El SAT aún no ha publicado las tarifas fiscales para el ejercicio {ejercicio}.
          Los períodos de {ejercicio} no se pueden calcular hasta que las tarifas se capturen en el sistema.
        </p>
      </div>
    </div>
  );
}

export function PrivacyReviewBanner() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[var(--color-azul)]/20 bg-[var(--color-primary-light)] p-4 text-sm">
      <Shield className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-azul)]" />
      <div>
        <p className="font-medium text-blue-900 dark:text-blue-200">
          Aviso de privacidad en revisión
        </p>
        <p className="mt-1 text-blue-800/80 dark:text-blue-300/80">
          El aviso de privacidad y los términos de servicio se encuentran en revisión legal
          para su conformidad con la LFPDPPP. El documento definitivo será publicado antes
          del lanzamiento público.
        </p>
      </div>
    </div>
  );
}
