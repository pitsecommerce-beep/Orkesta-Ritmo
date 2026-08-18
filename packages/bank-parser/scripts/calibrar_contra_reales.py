#!/usr/bin/env python3
"""Calibra el parser bancario contra estados de cuenta reales.

Recorre tests/fixtures/reales/ y parsea cada archivo encontrado
(PDF o TXT), imprimiendo un reporte estructurado de lo que se extrajo.

Uso:
    cd packages/bank-parser
    PYTHONPATH=src python scripts/calibrar_contra_reales.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

REALES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "reales"

EXTENSIONES_SOPORTADAS = {".pdf", ".txt", ".csv"}


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

    from bank_parser.adapters.mercado_pago import parsea_texto_mercado_pago
    from bank_parser.detector import detecta_institucion

    archivos = sorted(
        f for f in REALES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONES_SOPORTADAS
    ) if REALES_DIR.exists() else []

    if not archivos:
        print("=" * 60)
        print("  No hay fixtures reales para calibrar.")
        print(f"  Directorio: {REALES_DIR}")
        print("  Coloque archivos PDF/TXT/CSV de estados de cuenta reales")
        print("  en ese directorio.")
        print("=" * 60)
        return 0

    errores_totales = 0

    for archivo in archivos:
        print(f"\n{'=' * 60}")
        print(f"  {archivo.name}")
        print(f"{'=' * 60}")

        try:
            if archivo.suffix.lower() == ".txt":
                texto = archivo.read_text(encoding="utf-8")
                extracto = parsea_texto_mercado_pago(texto)
            elif archivo.suffix.lower() == ".pdf":
                adaptador = detecta_institucion(archivo)
                print(f"  institucion detectada: {adaptador.institucion}")
                extracto = adaptador.parsea(archivo)
            else:
                print(f"  Formato no soportado para parseo directo: {archivo.suffix}")
                continue
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            errores_totales += 1
            continue

        print(f"  institucion:     {extracto.institucion}")
        print(f"  titular:         {extracto.titular}")
        print(f"  cuenta:          {extracto.identificador_cuenta}")
        print(f"  periodo:         {extracto.periodo_inicio} — {extracto.periodo_fin}")
        print(f"  saldo_inicial:   {extracto.saldo_inicial}")
        print(f"  saldo_final:     {extracto.saldo_final}")
        print(f"  total_abonos:    {extracto.total_abonos_declarado}")
        print(f"  total_cargos:    {extracto.total_cargos_declarado}")
        print(f"  comisiones:      {extracto.comisiones_declaradas}")
        print(f"  movimientos:     {len(extracto.movimientos)}")
        print(f"  pares_espejo:    {extracto.pares_espejo}")
        print(f"  es_confiable:    {extracto.es_confiable}")
        print(f"  abono_neto:      {extracto.abono_neto}")
        print(f"  cargo_neto:      {extracto.cargo_neto}")

        if extracto.alertas:
            print(f"\n  Alertas ({len(extracto.alertas)}):")
            for alerta in extracto.alertas:
                print(f"    - {alerta}")

        vacios = []
        for campo in ["titular", "identificador_cuenta", "periodo_inicio",
                       "periodo_fin", "saldo_inicial", "saldo_final"]:
            val = getattr(extracto, campo, None)
            if val is None or val == "" or val == Decimal("0"):
                vacios.append(campo)

        if vacios:
            print(f"\n  Campos vacios o cero: {', '.join(vacios)}")

        movs_sin_id = sum(1 for m in extracto.movimientos if not m.identificador_transaccion)
        movs_sin_cat = sum(1 for m in extracto.movimientos if not m.categoria)
        if movs_sin_id:
            print(f"  Movimientos sin ID transaccion: {movs_sin_id}")
        if movs_sin_cat:
            print(f"  Movimientos sin categoria: {movs_sin_cat}")

    print(f"\n{'=' * 60}")
    print(f"  Resumen: {len(archivos)} archivos, {errores_totales} errores")
    print(f"{'=' * 60}")

    return 1 if errores_totales > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
