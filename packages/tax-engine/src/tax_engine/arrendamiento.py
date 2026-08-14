"""
Cálculo de ISR para régimen de Arrendamiento.

Arrendamiento es un pago provisional mensual (o trimestral):
- Ingreso del periodo (mensual o trimestral), NUNCA acumulado desde enero.
- Deducción opcional del 35% del ingreso (Art. 115 LISR).
- Base gravable = ingreso - deducción.
- ISR se calcula con tarifa Art. 96: (base - lim_inf) * % + cuota_fija.
- Se restan retenciones de ISR (10% cuando se factura a persona moral).

Para trimestral: la tarifa mensual se triplica en cuota fija y límites.
"""

from decimal import Decimal

from tax_engine.clasificador import CfdiClasificado
from tax_engine.exceptions import EjercicioNoDisponibleError
from tax_engine.tarifas_fallback import buscar_tramo_art96
from tax_engine.types import (
    DesgloseISR,
    TramoArt96,
    TrazabilidadCfdi,
)


def _triplicar_tarifa(tarifas: list[TramoArt96]) -> list[TramoArt96]:
    """
    Triplica la tarifa mensual del Art. 96 para opcion trimestral.

    Multiplica limite_inferior, limite_superior y cuota_fija por 3.
    El porcentaje se mantiene igual.
    """
    resultado = []
    for tramo in tarifas:
        resultado.append(
            TramoArt96(
                limite_inferior=tramo.limite_inferior * Decimal("3"),
                limite_superior=(
                    tramo.limite_superior * Decimal("3")
                    if tramo.limite_superior is not None
                    else None
                ),
                cuota_fija=tramo.cuota_fija * Decimal("3"),
                porcentaje=tramo.porcentaje,
            )
        )
    return resultado


def calcular_isr_arrendamiento(
    cfdis_clasificados: list[CfdiClasificado],
    tarifas_art96: list[TramoArt96],
    tipo_deduccion: str = "opcional",
    opcion_trimestral: bool = False,
) -> tuple[DesgloseISR, list[str]]:
    """
    Calcula el ISR provisional para regimen de Arrendamiento.

    Args:
        cfdis_clasificados: CFDIs clasificados del periodo (mes o trimestre).
        tarifas_art96: Tarifa Art. 96 mensual del ejercicio.
        tipo_deduccion: Tipo de deduccion ("ciega" = 35%).
        opcion_trimestral: True si el contribuyente ejerce opcion trimestral.

    Returns:
        Tupla de (DesgloseISR, alertas).
    """
    if not tarifas_art96:
        raise EjercicioNoDisponibleError(0, "No tiene tarifas Art. 96 cargadas.")

    alertas: list[str] = []
    trazabilidad: list[TrazabilidadCfdi] = []

    # Si es trimestral, triplicar la tarifa
    tarifas_aplicables = (
        _triplicar_tarifa(tarifas_art96) if opcion_trimestral else tarifas_art96
    )

    # Sumar ingresos del periodo
    ingresos = Decimal("0")
    retenciones_isr = Decimal("0")

    for cfdi in cfdis_clasificados:
        if not cfdi.considerado:
            continue

        ingresos += cfdi.ingreso_base
        retenciones_isr += cfdi.isr_retenido

        trazabilidad.extend(cfdi.trazabilidad)

    # Calcular deduccion
    if tipo_deduccion == "opcional":
        deducciones = ingresos * Decimal("35") / Decimal("100")
    else:
        alertas.append(
            f"Tipo de deducción '{tipo_deduccion}' no soportado. "
            f"Usando deducción opcional (35%)."
        )
        deducciones = ingresos * Decimal("35") / Decimal("100")

    # Base gravable
    base_gravable = ingresos - deducciones

    # Calcular ISR con tarifa Art. 96
    impuesto_determinado = Decimal("0")

    if base_gravable > Decimal("0"):
        tramo = buscar_tramo_art96(base_gravable, tarifas_aplicables)

        if tramo is None:
            alertas.append(
                f"Base gravable ({base_gravable}) no encaja en ningún tramo "
                f"de la tarifa Art. 96."
            )
        else:
            excedente = base_gravable - tramo.limite_inferior
            impuesto_excedente = excedente * tramo.porcentaje / Decimal("100")
            impuesto_determinado = impuesto_excedente + tramo.cuota_fija

    # ISR a pagar
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
