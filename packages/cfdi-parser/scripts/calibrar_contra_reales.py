#!/usr/bin/env python3
"""Calibra el parser de CFDI contra fixtures reales.

Recorre tests/fixtures/reales/ y parsea cada XML encontrado,
imprimiendo un reporte estructurado de lo que se extrajo.

Uso:
    cd packages/cfdi-parser
    PYTHONPATH=src python scripts/calibrar_contra_reales.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REALES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "reales"


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

    from cfdi_parser.source import detect_and_parse
    from cfdi_parser.validator import validate_cfdi_xml

    xmls = sorted(REALES_DIR.glob("*.xml"))

    if not xmls:
        print("=" * 60)
        print("  No hay fixtures reales para calibrar.")
        print(f"  Directorio: {REALES_DIR}")
        print("  Coloque archivos XML de CFDI reales en ese directorio.")
        print("=" * 60)
        return 0

    errores_totales = 0

    for xml_path in xmls:
        print(f"\n{'=' * 60}")
        print(f"  {xml_path.name}")
        print(f"{'=' * 60}")

        xml_bytes = xml_path.read_bytes()
        resultado = detect_and_parse(xml_bytes)

        print(f"  tipo:      {resultado.tipo}")
        print(f"  es_valido: {resultado.es_valido}")

        if resultado.errores:
            print(f"  errores:   {resultado.errores}")
            errores_totales += len(resultado.errores)

        data = resultado.data
        if data is None:
            print("  data:      None (parseo fallido)")
            continue

        attrs = vars(data) if hasattr(data, "__dict__") else {}
        if hasattr(data, "__dataclass_fields__"):
            attrs = {f: getattr(data, f) for f in data.__dataclass_fields__}

        vacios = []
        for campo, valor in attrs.items():
            representacion = repr(valor)
            if len(representacion) > 120:
                representacion = representacion[:117] + "..."
            print(f"  {campo}: {representacion}")
            if valor is None or valor == "" or valor == 0:
                vacios.append(campo)

        if vacios:
            print(f"\n  Campos vacios o cero: {', '.join(vacios)}")

        validacion = validate_cfdi_xml(xml_bytes)
        if validacion:
            print(f"\n  Advertencias de validacion:")
            for v in validacion:
                print(f"    - {v}")

    print(f"\n{'=' * 60}")
    print(f"  Resumen: {len(xmls)} archivos, {errores_totales} errores de parseo")
    print(f"{'=' * 60}")

    return 1 if errores_totales > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
