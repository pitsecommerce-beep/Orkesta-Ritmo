#!/usr/bin/env python3
"""Calibra la extraccion de constancia contra PDFs reales del SAT.

Recorre tests/fixtures/reales/ y parsea cada PDF encontrado,
imprimiendo un reporte estructurado de lo que se extrajo.

Uso:
    cd packages/tax-engine
    PYTHONPATH=src python scripts/calibrar_contra_reales.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REALES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "reales"


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

    from tax_engine.constancia import extraer_constancia_desde_pdf

    pdfs = sorted(REALES_DIR.glob("*.pdf"))

    if not pdfs:
        print("=" * 60)
        print("  No hay fixtures reales para calibrar.")
        print(f"  Directorio: {REALES_DIR}")
        print("  Coloque archivos PDF de constancias del SAT reales")
        print("  en ese directorio.")
        print("=" * 60)
        return 0

    errores_totales = 0

    for pdf_path in pdfs:
        print(f"\n{'=' * 60}")
        print(f"  {pdf_path.name}")
        print(f"{'=' * 60}")

        try:
            resultado = extraer_constancia_desde_pdf(pdf_path)
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            errores_totales += 1
            continue

        print(f"  rfc:            {resultado.rfc}")
        print(f"  nombre:         {resultado.nombre}")
        print(f"  tipo_persona:   {resultado.tipo_persona}")
        print(f"  codigo_postal:  {resultado.codigo_postal}")
        print(f"  fecha_inicio:   {resultado.fecha_inicio_operaciones}")

        if resultado.regimenes:
            print(f"\n  Regimenes ({len(resultado.regimenes)}):")
            for reg in resultado.regimenes:
                print(f"    - {reg.descripcion}")
                print(f"      clave_sat: {reg.clave_sat}, vigente: {reg.vigente}")
                print(f"      fecha_alta: {reg.fecha_alta}")
        else:
            print("  Regimenes: NINGUNO EXTRAIDO")
            errores_totales += 1

        if resultado.obligaciones:
            print(f"\n  Obligaciones ({len(resultado.obligaciones)}):")
            for obl in resultado.obligaciones:
                print(f"    - {obl.descripcion}")
                print(f"      periodicidad: {obl.periodicidad}, fecha_inicio: {obl.fecha_inicio}")
        else:
            print("  Obligaciones: NINGUNA EXTRAIDA")

        vacios = []
        for campo in ["rfc", "nombre", "tipo_persona"]:
            val = getattr(resultado, campo, None)
            if val is None or val == "":
                vacios.append(campo)

        if vacios:
            print(f"\n  Campos vacios: {', '.join(vacios)}")
            errores_totales += 1

    print(f"\n{'=' * 60}")
    print(f"  Resumen: {len(pdfs)} archivos, {errores_totales} errores")
    print(f"{'=' * 60}")

    return 1 if errores_totales > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
