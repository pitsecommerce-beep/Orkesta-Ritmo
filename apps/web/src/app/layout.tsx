import type { Metadata } from "next";
import { Montserrat, Lora } from "next/font/google";
import { EnvChecker } from "@/components/EnvChecker";
import "./globals.css";

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  display: "swap",
});

const lora = Lora({
  variable: "--font-lora",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Orkesta Ritmo — Prepara tu declaración fiscal",
  description:
    "Calcula tus impuestos mensuales y provisionales con trazabilidad CFDI por CFDI. Ritmo prepara, tú presentas.",
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${montserrat.variable} ${lora.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <EnvChecker />
        {children}
      </body>
    </html>
  );
}
