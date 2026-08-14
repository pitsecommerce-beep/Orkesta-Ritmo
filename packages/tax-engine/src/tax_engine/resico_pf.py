"""
Calculo de ISR para RESICO Persona Fisica.

RESICO PF es un pago definitivo mensual:
- Se calcula sobre el ingreso mensual total de CFDIs clasificados.
- Se busca la tasa aplicable en la tarifa RESICO por tramo.
- ISR = ingreso * tasa del tramo.
- Se restan las retenciones de ISR del periodo.
- Si el ingreso excede el ultimo tramo, se genera una alerta.
"""

from decimal import Decimal

from tax_engine.clasificador import CfdiClasificado
from tax_engine.tarifas_fallback import buscar_tramo_resico
from tax_engine.types import (
    DesgloseISR,
    TramoResico,
    TrazabilidadCfdi,
)


def calcular_isr_resico_pf(
    cfdis_clasificados: list[CfdiClasificado],
    tarifas_resico: list[TramoResico],
) -> tuple[DesgloseISR, list[str]]:
    """
    Calcula el ISR para RESICO Persona Fisica en un periodo mensual.

    Args:
        cfdis_clasificados: CFDIs ya clasificados y filtrados para el periodo.
        tarifas_resico: Tarifa RESICO del ejercicio.

    Returns:
        Tupla de (DesgloseISR, alertas).
    """
    alertas: list[str] = []
    trazabilidad: list[TrazabilidadCfdi] = []

    # Sumar ingresos de CFDIs considerados
    ingresos = Decimal("0")
    retenciones_isr = Decimal("0")

    for cfdi in cfdis_clasificados:
        if not cfdi.considerado:
            continue

        ingresos += cfdi.ingreso_base
        retenciones_isr += cfdi.isr_retenido

        trazabilidad.extend(cfdi.trazabilidad)

    # En RESICO PF no hay deducciones
    deducciones = Decimal("0")
    base_gravable = ingresos

    # Buscar tramo aplicable
    impuesto_determinado = Decimal("0")

    if base_gravable > Decimal("0"):
        tramo = buscar_tramo_resico(base_gravable, tarifas_resico)

        if tramo is None:
            # Ingreso excede el limite superior del ultimo tramo
            alertas.append(
                f"Ingreso mensual ({base_gravable}) excede el limite maximo "
                f"de la tarifa RESICO. Verificar si el contribuyente debe "
                f"cambiar de regimen."
            )
            # Aplicar la tasa del ultimo tramo como mejor estimacion
            if tarifas_resico:
                ultimo_tramo = tarifas_resico[-1]
                impuesto_determinado = base_gravable * ultimo_tramo.tasa / Decimal("100")
                alertas.append(
                    f"Se aplico la tasa del ultimo tramo ({ultimo_tramo.tasa}%) "
                    f"como estimacion."
                )
        else:
            impuesto_determinado = base_gravable * tramo.tasa / Decimal("100")

    isr_a_cargo = impuesto_determinado - retenciones_isr
    if isr_a_cargo < Decimal("0"):
        alertas.append(
            f"Retenciones ISR ({retenciones_isr}) superan el impuesto "
            f"determinado ({impuesto_determinado}). Saldo a favor: "
            f"{abs(isr_a_cargo)}"
        )

    desglose = DesgloseISR(
        ingresos=ingresos,
        deducciones=deducciones,
        base_gravable=base_gravable,
        impuesto_determinado=impuesto_determinado,
        retenciones_isr=retenciones_isr,
        isr_a_cargo=isr_a_cargo,
        trazabilidad=trazabilidad,
    )

    return desglose, alertas
