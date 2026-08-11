"use client";

import Image from "next/image";

type LogoProps = {
  variant?: "dark" | "white" | "blue";
  type?: "iso" | "full";
  className?: string;
};

const SRCS: Record<string, Record<string, string>> = {
  iso: {
    dark: "/brand/isotipo-dark.svg",
    white: "/brand/isotipo-white.svg",
    blue: "/brand/isotipo-blue.svg",
  },
  full: {
    dark: "/brand/logotipo-dark.svg",
    white: "/brand/logotipo-white.svg",
    blue: "/brand/logotipo-blue.svg",
  },
};

export function Logo({ variant = "dark", type = "full", className }: LogoProps) {
  const src = SRCS[type][variant];
  const w = type === "iso" ? 40 : 160;
  const h = type === "iso" ? 40 : 40;

  return (
    <Image
      src={src}
      alt="Orkesta Ritmo"
      width={w}
      height={h}
      className={className}
      priority
    />
  );
}
