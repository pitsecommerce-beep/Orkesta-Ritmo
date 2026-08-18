#!/usr/bin/env python3
"""Runner del harness de evals conversacionales.

Hoy el modulo conversacional no tiene proveedor de IA — este runner
solo valida que la estructura de los casos es correcta y reporta
cuantos estan listos vs cuantos son ejemplos estructurales.

Cuando se conecte un proveedor, este runner:
1. Cargara los casos de casos.py
2. Enviara cada entrada al endpoint /chat/mensaje (o al modulo directo)
3. Verificara la salida contra los criterios definidos
4. Reportara pass/fail con detalle

Uso:
    cd apps/api
    PYTHONPATH=. python tests/evals/run_evals.py
"""

from __future__ import annotations

import sys


def main() -> int:
    from tests.evals.casos import CASOS_EVAL

    total = len(CASOS_EVAL)
    ejemplos = sum(1 for c in CASOS_EVAL if c.get("es_ejemplo_estructural"))
    reales = total - ejemplos

    print("=" * 60)
    print("  Harness de evals — modulo conversacional")
    print("=" * 60)
    print(f"  Casos totales:               {total}")
    print(f"  Ejemplos estructurales:      {ejemplos}")
    print(f"  Evals reales:                {reales}")
    print()

    if reales == 0:
        print("  ESTADO: No hay evals reales.")
        print("  El modulo conversacional no tiene proveedor de IA conectado.")
        print("  Los casos existentes son ejemplos de formato.")
        print()
        print("  Para activar evals reales:")
        print("    1. Configurar LLM_PROVIDER y la llave correspondiente")
        print("    2. Implementar la llamada al proveedor en chat.py")
        print("    3. Escribir 30-50 casos reales en casos.py")
        print("=" * 60)
        return 0

    print("  Validando estructura de casos...")
    campos_requeridos = {"id", "categoria", "entrada", "salida_esperada", "criterios"}
    errores = 0

    for caso in CASOS_EVAL:
        faltantes = campos_requeridos - set(caso.keys())
        if faltantes:
            print(f"  ERROR: caso {caso.get('id', '???')} le faltan: {faltantes}")
            errores += 1

    if errores:
        print(f"\n  {errores} caso(s) con estructura invalida.")
        return 1

    print(f"  Todos los {total} casos tienen estructura valida.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
