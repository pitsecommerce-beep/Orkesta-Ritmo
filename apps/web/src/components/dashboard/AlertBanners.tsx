"use client";

import { AlertTriangle, Shield } from "lucide-react";

export function TarifaAlertBanner({ ejercicio = 2026 }: { ejercicio?: number }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-sm dark:border-yellow-900/50 dark:bg-yellow-950/30">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-yellow-600 dark:text-yellow-500" />
      <div>
        <p className="font-medium text-yellow-900 dark:text-yellow-200">
          Tarifas {ejercicio} no disponibles
        </p>
        <p className="mt-1 text-yellow-800 dark:text-yellow-300/80">
          El SAT aún no ha publicado las tarifas fiscales para el ejercicio {ejercicio}.
          Los períodos de {ejercicio} no se pueden calcular hasta que las tarifas se capturen en el sistema.
        </p>
      </div>
    </div>
  );
}

export function PrivacyReviewBanner() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm dark:border-blue-900/50 dark:bg-blue-950/30">
      <Shield className="mt-0.5 h-5 w-5 shrink-0 text-blue-600 dark:text-blue-400" />
      <div>
        <p className="font-medium text-blue-900 dark:text-blue-200">
          Aviso de privacidad en revisión
        </p>
        <p className="mt-1 text-blue-800 dark:text-blue-300/80">
          El aviso de privacidad y los términos de servicio se encuentran en revisión legal
          para su conformidad con la LFPDPPP. El documento definitivo será publicado antes
          del lanzamiento público.
        </p>
      </div>
    </div>
  );
}
