import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos y Condiciones — Orkesta Ritmo",
};

export default function TerminosPage() {
  return (
    <div className="min-h-full">
      <header className="border-b">
        <div className="mx-auto flex h-16 max-w-4xl items-center px-4">
          <Link href="/"><Logo type="full" /></Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="font-heading text-3xl font-bold">Términos y Condiciones</h1>
        <p className="mt-2 text-sm text-muted-foreground">Última actualización: enero 2025</p>

        <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted-foreground">
          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">1. Naturaleza del servicio</h2>
            <p className="mt-2">
              Orkesta Ritmo (&quot;Ritmo&quot;) es una herramienta de preparación fiscal. Ritmo calcula
              impuestos y genera desgloses, pero <strong>no es un despacho contable, no presta
              servicios de asesoría fiscal y no presenta declaraciones ante el SAT</strong>.
              La responsabilidad de presentar la declaración es exclusivamente del contribuyente.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">2. Limitaciones</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>Ritmo no genera línea de captura</li>
              <li>Ritmo no se conecta al SAT ni a YCloud</li>
              <li>Ritmo no procesa pagos de impuestos</li>
              <li>Los cálculos son informativos y deben ser verificados por el contribuyente</li>
            </ul>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">3. Regímenes soportados</h2>
            <p className="mt-2">
              Ritmo soporta exclusivamente: RESICO Persona Física, RESICO PF con Sueldos,
              Arrendamiento y Arrendamiento con Sueldos.
              Cualquier otro régimen será dirigido a una lista de espera.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">4. Privacidad y seguridad</h2>
            <p className="mt-2">
              El tratamiento de datos personales se rige por nuestro{" "}
              <Link href="/privacidad" className="underline text-foreground">Aviso de Privacidad</Link>.
              Material de e.firma nunca se transmite a proveedores de inteligencia artificial.
              Datos identificables (RFC, CURP, CLABE) se enmascaran antes de cualquier llamada externa.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">5. Propiedad intelectual</h2>
            <p className="mt-2">
              Orkesta Ritmo, su motor fiscal, marca y diseño son propiedad de Orkesta Labs, S.A.P.I. de C.V.
              Los datos fiscales del usuario permanecen propiedad del usuario.
            </p>
          </section>

          <section>
            <h2 className="font-heading text-lg font-semibold text-foreground">6. Jurisdicción</h2>
            <p className="mt-2">
              Estos términos se rigen por las leyes de los Estados Unidos Mexicanos.
              Cualquier controversia se resolverá ante los tribunales competentes de la Ciudad de México.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
