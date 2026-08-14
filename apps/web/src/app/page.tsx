import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { CookieConsent } from "@/components/CookieConsent";
import {
  Shield,
  FileText,
  Calculator,
  Upload,
  CheckCircle,
  Lock,
  ChevronDown,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const REGIMES = [
  { name: "RESICO Persona Física", desc: "Régimen Simplificado de Confianza para personas físicas con ingresos hasta 3.5 MDP anuales." },
  { name: "RESICO PF + Sueldos", desc: "RESICO combinado con ingresos por sueldos y salarios. Los sueldos no tributan en RESICO; se acumulan por separado." },
  { name: "Arrendamiento", desc: "Ingresos por renta de inmuebles con deducción opcional del 35% o deducciones comprobables." },
  { name: "Arrendamiento + Sueldos", desc: "Arrendamiento combinado con ingresos por sueldos y salarios." },
];

const STEPS = [
  { icon: Upload, title: "Sube tus CFDI", desc: "Carga tus XMLs o conéctate a tu PAC para descargarlos." },
  { icon: Calculator, title: "Ritmo calcula", desc: "Motor fiscal determinista con trazabilidad CFDI por CFDI." },
  { icon: FileText, title: "Revisa el desglose", desc: "Verifica cada línea: base, tasa, impuesto, retención." },
  { icon: CheckCircle, title: "Tú presentas en SAT", desc: "Descarga tu pre-declaración y preséntala en el portal del SAT." },
];

const FAQ = [
  { q: "¿Ritmo presenta mi declaración?", a: "No. Ritmo prepara los cálculos y te muestra el desglose. Tú presentas directamente en el portal del SAT." },
  { q: "¿Conectan con el SAT?", a: "No. Nunca nos conectamos al SAT ni generamos línea de captura. Tu e.firma nunca sale de tu dispositivo." },
  { q: "¿Qué regímenes soportan?", a: "RESICO PF, RESICO PF + Sueldos, Arrendamiento y Arrendamiento + Sueldos. Si tienes otro régimen, puedes registrarte en la lista de espera." },
  { q: "¿Mis datos están seguros?", a: "Sí. Cifrado AES-256-GCM, aislamiento por tenant, y nunca enviamos tu RFC o CURP real a proveedores de IA." },
  { q: "¿Es gratis?", a: "Ritmo tiene un plan gratuito con funcionalidad limitada. Los planes de pago desbloquean más períodos y funciones avanzadas." },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-full">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Logo type="full" />
          <nav className="hidden gap-6 md:flex">
            <a href="#como-funciona" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Cómo funciona
            </a>
            <a href="#regimenes" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Regímenes
            </a>
            <a href="#seguridad" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Seguridad
            </a>
            <a href="#faq" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              FAQ
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/auth/login">
              <Button variant="outline" size="sm">Iniciar sesión</Button>
            </Link>
            <Link href="/auth/login">
              <Button size="sm">Comenzar gratis</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[var(--color-azul-claro)]/20 to-background py-24 md:py-36">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <h1 className="animate-fade-in-up font-heading text-4xl font-bold tracking-tight text-foreground md:text-6xl">
            Prepara tu declaración fiscal,{" "}
            <span className="text-[var(--color-azul)]">sin sorpresas</span>
          </h1>
          <p className="animate-fade-in-up stagger-2 mx-auto mt-6 max-w-2xl text-lg text-muted-foreground md:text-xl">
            Ritmo calcula tus impuestos mensuales con trazabilidad CFDI por CFDI.
            Tú revisas, tú presentas en el portal del SAT.
          </p>
          <div className="animate-fade-in-up stagger-4 mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/auth/login">
              <Button size="lg" className="gap-2 px-8 transition-transform hover:scale-105">
                Comenzar gratis <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#como-funciona">
              <Button variant="outline" size="lg" className="gap-2 px-8 transition-transform hover:scale-105">
                Ver cómo funciona <ChevronDown className="h-4 w-4" />
              </Button>
            </a>
          </div>
          <p className="animate-fade-in stagger-6 mt-6 text-xs text-muted-foreground">
            Ritmo prepara, tú presentas. No generamos línea de captura ni conectamos con el SAT.
          </p>
        </div>
      </section>

      {/* Problem */}
      <section className="border-b py-16 md:py-24">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <h2 className="font-heading text-2xl font-bold md:text-3xl">
            ¿Cuánto tiempo pasas cada mes armando tu declaración?
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            Descargar CFDIs, clasificar ingresos, calcular retenciones, cruzar con pagos...
            son horas que podrías dedicar a tu negocio. Ritmo automatiza el cálculo y te muestra
            exactamente de dónde sale cada número.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section id="como-funciona" className="py-16 md:py-24">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center font-heading text-2xl font-bold md:text-3xl">
            Cómo funciona
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-azul)]/10">
                  <s.icon className="h-7 w-7 text-[var(--color-azul)]" />
                </div>
                <div className="mt-2 flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-azul)] text-xs font-bold text-white">
                  {i + 1}
                </div>
                <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What Ritmo does / doesn't */}
      <section className="border-t bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-4">
          <h2 className="text-center font-heading text-2xl font-bold md:text-3xl">
            Qué hace Ritmo — y qué no
          </h2>
          <div className="mt-12 grid gap-8 md:grid-cols-2">
            <Card className="card-hover">
              <CardContent className="pt-6">
                <h3 className="font-heading text-lg font-semibold text-green-700">Sí hace</h3>
                <ul className="mt-4 space-y-2 text-sm">
                  <li className="flex gap-2"><CheckCircle className="h-4 w-4 shrink-0 text-green-600 mt-0.5" /> Calcula ISR, IVA, retenciones con trazabilidad CFDI por CFDI</li>
                  <li className="flex gap-2"><CheckCircle className="h-4 w-4 shrink-0 text-green-600 mt-0.5" /> Clasifica automáticamente tus comprobantes</li>
                  <li className="flex gap-2"><CheckCircle className="h-4 w-4 shrink-0 text-green-600 mt-0.5" /> Concilia contra estados de cuenta bancarios</li>
                  <li className="flex gap-2"><CheckCircle className="h-4 w-4 shrink-0 text-green-600 mt-0.5" /> Genera el desglose listo para capturar en SAT</li>
                  <li className="flex gap-2"><CheckCircle className="h-4 w-4 shrink-0 text-green-600 mt-0.5" /> Acumula subsidio al empleo y nómina</li>
                </ul>
              </CardContent>
            </Card>
            <Card className="card-hover">
              <CardContent className="pt-6">
                <h3 className="font-heading text-lg font-semibold text-red-700">No hace</h3>
                <ul className="mt-4 space-y-2 text-sm">
                  <li className="flex gap-2"><Shield className="h-4 w-4 shrink-0 text-red-600 mt-0.5" /> No presenta tu declaración — tú lo haces en sat.gob.mx</li>
                  <li className="flex gap-2"><Shield className="h-4 w-4 shrink-0 text-red-600 mt-0.5" /> No genera línea de captura</li>
                  <li className="flex gap-2"><Shield className="h-4 w-4 shrink-0 text-red-600 mt-0.5" /> No conecta con el SAT ni con YCloud</li>
                  <li className="flex gap-2"><Shield className="h-4 w-4 shrink-0 text-red-600 mt-0.5" /> No procesa pagos</li>
                  <li className="flex gap-2"><Shield className="h-4 w-4 shrink-0 text-red-600 mt-0.5" /> No envía tu e.firma a ningún proveedor externo</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Regimes */}
      <section id="regimenes" className="py-16 md:py-24">
        <div className="mx-auto max-w-5xl px-4">
          <h2 className="text-center font-heading text-2xl font-bold md:text-3xl">
            Regímenes fiscales soportados
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-muted-foreground">
            Si tu régimen no aparece aquí, regístrate en la lista de espera y te avisamos cuando lo soportemos.
          </p>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {REGIMES.map((r) => (
              <Card key={r.name} className="card-hover">
                <CardContent className="pt-6">
                  <h3 className="font-heading font-semibold">{r.name}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{r.desc}</p>
                </CardContent>
              </Card>
            ))}
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center pt-6 text-center">
                <p className="font-heading font-semibold text-muted-foreground">¿Otro régimen?</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Regístrate en la lista de espera.
                </p>
                <Link href="/lista-espera" className="mt-3">
                  <Button variant="outline" size="sm">Lista de espera</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Security */}
      <section id="seguridad" className="border-t bg-muted/30 py-16 md:py-24">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <Lock className="mx-auto h-10 w-10 text-[var(--color-azul)]" />
          <h2 className="mt-4 font-heading text-2xl font-bold md:text-3xl">
            Seguridad desde el diseño
          </h2>
          <div className="mt-10 grid gap-6 text-left sm:grid-cols-2">
            <div>
              <h3 className="font-heading font-semibold">Cifrado AES-256-GCM</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Tu e.firma se cifra con envelope encryption. La llave maestra nunca se almacena junto a los datos.
              </p>
            </div>
            <div>
              <h3 className="font-heading font-semibold">Aislamiento por tenant</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Row-Level Security en cada tabla. Un contribuyente nunca ve datos de otro.
              </p>
            </div>
            <div>
              <h3 className="font-heading font-semibold">PII nunca llega a la IA</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Middleware de enmascaramiento reemplaza RFC, CURP y CLABE antes de cualquier llamada a proveedores de IA.
              </p>
            </div>
            <div>
              <h3 className="font-heading font-semibold">E.firma protegida</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Material de e.firma nunca se envía a proveedores externos. Detección activa bloquea cualquier intento.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-16 md:py-24">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="text-center font-heading text-2xl font-bold md:text-3xl">
            Preguntas frecuentes
          </h2>
          <div className="mt-10 space-y-6">
            {FAQ.map((f) => (
              <div key={f.q}>
                <h3 className="font-heading font-semibold">{f.q}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{f.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t bg-[var(--color-azul)] py-16 text-white">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="font-heading text-2xl font-bold md:text-3xl">
            Empieza a preparar tu declaración hoy
          </h2>
          <p className="mt-3 text-white/80">
            Crea tu cuenta gratis. Sin tarjeta de crédito, sin compromisos.
          </p>
          <Link href="/auth/login">
            <Button size="lg" variant="secondary" className="mt-8 gap-2 px-8">
              Crear cuenta gratis <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 md:flex-row md:justify-between">
          <div className="flex items-center gap-3">
            <Logo type="iso" className="h-8 w-8" />
            <span className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} Orkesta Labs, S.A.P.I. de C.V.
            </span>
          </div>
          <nav className="flex gap-6 text-sm text-muted-foreground">
            <Link href="/privacidad" className="hover:text-foreground">Aviso de privacidad</Link>
            <Link href="/terminos" className="hover:text-foreground">Términos</Link>
          </nav>
        </div>
      </footer>

      <CookieConsent />
    </div>
  );
}
