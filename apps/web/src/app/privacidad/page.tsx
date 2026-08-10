import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aviso de Privacidad — Orkesta Ritmo",
};

export default function PrivacidadPage() {
  return (
    <div className="min-h-full">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-4xl items-center px-4">
          <Link href="/"><Logo type="full" /></Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="font-heading text-3xl font-bold">Aviso de Privacidad</h1>
        <p className="mt-2 text-sm text-muted-foreground">Última actualización: enero 2025</p>

        <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted-foreground">
          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Identidad del responsable</h2>
            <p className="mt-2">
              Orkesta Labs, S.A.P.I. de C.V. (&quot;Orkesta&quot;), con domicilio en Ciudad de México, México,
              es responsable del tratamiento de sus datos personales conforme a la Ley Federal de Protección
              de Datos Personales en Posesión de los Particulares (LFPDPPP).
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Datos que recabamos</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Datos de identificación: nombre, correo electrónico, RFC</li>
              <li>Datos fiscales: comprobantes CFDI (XML), estados de cuenta bancarios</li>
              <li>Datos de uso: páginas visitadas, acciones realizadas en la plataforma</li>
            </ul>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Finalidades del tratamiento</h2>
            <p className="mt-2">
              Utilizamos sus datos para: (i) calcular impuestos y generar pre-declaraciones;
              (ii) autenticar su identidad; (iii) mejorar nuestros servicios;
              (iv) cumplir con obligaciones legales.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Protección de datos</h2>
            <p className="mt-2">
              Implementamos cifrado AES-256-GCM para datos sensibles, aislamiento por tenant con
              Row-Level Security, y enmascaramiento de PII (RFC, CURP, CLABE) antes de cualquier
              comunicación con proveedores de inteligencia artificial. Su material de e.firma nunca
              se transmite a proveedores externos.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Derechos ARCO</h2>
            <p className="mt-2">
              Usted tiene derecho a Acceder, Rectificar, Cancelar u Oponerse al tratamiento de sus
              datos personales. Para ejercer estos derechos, envíe un correo a privacidad@orkesta.mx.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">Cookies</h2>
            <p className="mt-2">
              Utilizamos cookies esenciales para el funcionamiento del sitio. Las cookies de analítica
              están desactivadas por defecto y requieren su consentimiento explícito.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
