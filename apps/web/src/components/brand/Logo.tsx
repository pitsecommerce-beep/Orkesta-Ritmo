"use client";

import Image from "next/image";

type LogoProps = {
  variant?: "light" | "dark";
  type?: "iso" | "full";
  className?: string;
};

export function Logo({ variant = "light", type = "full", className }: LogoProps) {
  const src = type === "iso" ? "/brand/isotipo.svg" : "/brand/logotipo.svg";
  const w = type === "iso" ? 40 : 160;
  const h = type === "iso" ? 40 : 40;

  return (
    <Image
      src={src}
      alt="Orkesta Ritmo"
      width={w}
      height={h}
      className={`${variant === "dark" ? "invert" : ""} ${className ?? ""}`}
      priority
    />
  );
}
