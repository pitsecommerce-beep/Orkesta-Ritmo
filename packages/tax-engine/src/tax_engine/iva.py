"""
Calculo de IVA para todos los regimenes.

El IVA se calcula de forma uniforme para todos los regimenes:
- IVA trasladado: de CFDIs emitidos, usando la clasificacion de actividad.
- IVA retenido: suma de retenciones con impuesto="002".
- IVA acreditable: de CFDIs recibidos efectivamente pagados.
  Si no se puede determinar el pago, requiere_revision = True.
- IVA a pagar = trasladado - retenido - acreditable.

CFDIs de nomina NUNCA se mezclan con CFDIs de actividad para IVA.
"""

from decimal import Decimal
from typing import Optional

from tax_engine.clasificador import CfdiClasificado
from tax_engine.types import (
    CfdiNormalizado,
    DesgloseIVA,
    ResultadoActividad,
    ResultadoClasificacion,
    TrazabilidadCfdi,
)


def calcular_iva(
    cfdis_clasificados: list[CfdiClasificado],
    clasificaciones_actividad: Optional[list[ResultadoActividad]] = None,
    cfdis_recibidos: Optional[list[CfdiNormalizado]] = None,
) -> tuple[DesgloseIVA, list[str]]:
    """
    Calcula el IVA de un periodo para cualquier regimen.

    Args:
        cfdis_clasificados: CFDIs emitidos ya clasificados para el periodo.
        clasificaciones_actividad: Clasificacion de actividades para IVA.
            Si no se proporciona, se usa la tasa del CFDI directamente.
        cfdis_recibidos: CFDIs de gastos recibidos (para IVA acreditable).
            Si no se proporcionan, se marca requiere_revision.

    Returns:
        Tupla de (DesgloseIVA, alertas).
    """
    alertas: list[str] = []
    trazabilidad: list[TrazabilidadCfdi] = []

    # Mapa de clasificaciones por actividad_id
    mapa_clasificaciones: dict[str, ResultadoClasificacion] = {}
    if clasificaciones_actividad:
        for clasif in clasificaciones_actividad:
            mapa_clasificaciones[clasif.actividad_id] = clasif.resultado

    # Calcular IVA trasladado de CFDIs emitidos
    iva_trasladado = Decimal("0")
    iva_retenido = Decimal("0")

    for cfdi in cfdis_clasificados:
        if not cfdi.considerado:
            continue

        # Aplicar clasificacion de actividad si existe
        if cfdi.uuid in mapa_clasificaciones:
            resultado_act = mapa_clasificaciones[cfdi.uuid]
        elif clasificaciones_actividad:
            # Si hay clasificaciones pero este CFDI no tiene,
            # usar el IVA del documento
            resultado_act = None
        else:
            resultado_act = None

        if resultado_act == ResultadoClasificacion.EXENTO:
            # Actividad exenta: no genera IVA trasladado
            trazabilidad.append(
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto="IVA exento por clasificacion de actividad",
                    monto=Decimal("0"),
                )
            )
        elif resultado_act == ResultadoClasificacion.IVA0:
            # Tasa 0%: no genera IVA trasladado
            trazabilidad.append(
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto="IVA tasa 0% por clasificacion de actividad",
                    monto=Decimal("0"),
                )
            )
        elif resultado_act == ResultadoClasificacion.REVISAR:
            alertas.append(
                f"CFDI {cfdi.uuid}: actividad requiere revision para IVA."
            )
            # Incluir IVA del documento como esta
            iva_trasladado += cfdi.iva_trasladado
            trazabilidad.append(
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto="IVA trasladado (actividad pendiente de revision)",
                    monto=cfdi.iva_trasladado,
                )
            )
        elif resultado_act == ResultadoClasificacion.NO_APLICA:
            # No aplica IVA
            trazabilidad.append(
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto="IVA no aplica",
                    monto=Decimal("0"),
                )
            )
        else:
            # IVA16 o sin clasificacion: usar IVA del documento
            iva_trasladado += cfdi.iva_trasladado
            trazabilidad.append(
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto="IVA trasladado",
                    monto=cfdi.iva_trasladado,
                )
            )

        # Retenciones de IVA
        iva_retenido += cfdi.iva_retenido

    # IVA acreditable de CFDIs recibidos
    iva_acreditable = Decimal("0")
    requiere_revision = False
    motivo_revision: Optional[str] = None

    if cfdis_recibidos is None:
        # No se proporcionaron CFDIs recibidos:
        # no podemos determinar el IVA acreditable
        requiere_revision = True
        motivo_revision = (
            "No se proporcionaron CFDIs de gastos recibidos. "
            "IVA acreditable no determinado. "
            "Se requiere revision manual para determinar IVA acreditable."
        )
        alertas.append(motivo_revision)
    else:
        for cfdi_r in cfdis_recibidos:
            # Solo CFDIs vigentes
            if cfdi_r.estado == "cancelado":
                continue

            # Solo PUE o con complemento de pago demostrado
            if cfdi_r.tipo == "N":
                # Nomina nunca se mezcla
                continue

            if cfdi_r.tipo == "I" and cfdi_r.metodo_pago == "PUE":
                # PUE: efectivamente pagado
                for imp_t in cfdi_r.impuestos_trasladados:
                    if imp_t.impuesto == "002":
                        iva_acreditable += imp_t.importe
                        trazabilidad.append(
                            TrazabilidadCfdi(
                                uuid=cfdi_r.uuid,
                                concepto="IVA acreditable (gasto PUE)",
                                monto=imp_t.importe,
                            )
                        )
            elif cfdi_r.tipo == "I" and cfdi_r.metodo_pago == "PPD":
                # PPD sin complemento: no podemos acreditar
                if not requiere_revision:
                    requiere_revision = True
                    motivo_revision = (
                        "Existen CFDIs PPD recibidos sin complemento de pago verificado. "
                        "No se puede determinar si fueron efectivamente pagados."
                    )
                    alertas.append(motivo_revision)

    # IVA a pagar
    iva_a_pagar = iva_trasladado - iva_retenido - iva_acreditable

    desglose = DesgloseIVA(
        iva_trasladado=iva_trasladado,
        iva_retenido=iva_retenido,
        iva_acreditable=iva_acreditable,
        iva_a_pagar=iva_a_pagar,
        requiere_revision=requiere_revision,
        motivo_revision=motivo_revision,
        trazabilidad=trazabilidad,
    )

    return desglose, alertas
