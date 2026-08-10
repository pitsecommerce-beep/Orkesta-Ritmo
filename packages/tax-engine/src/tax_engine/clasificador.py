"""
Clasificador de CFDIs para calculo fiscal.

Determina cuales CFDIs deben considerarse en el calculo y
extrae los montos base aplicables segun el tipo y metodo de pago.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from tax_engine.types import (
    CfdiNormalizado,
    ImpuestoDR,
    ResultadoActividad,
    ResultadoClasificacion,
    TrazabilidadCfdi,
)


@dataclass
class CfdiClasificado:
    """Resultado de clasificar un CFDI para calculo."""
    uuid: str
    considerado: bool
    motivo: str
    ingreso_base: Decimal = Decimal("0")
    iva_trasladado: Decimal = Decimal("0")
    iva_retenido: Decimal = Decimal("0")
    isr_retenido: Decimal = Decimal("0")
    tasa_iva_aplicada: Optional[Decimal] = None
    es_pago: bool = False
    trazabilidad: list[TrazabilidadCfdi] = field(default_factory=list)


def _tasa_por_objeto_imp_dr(objeto_imp_dr: str, imp_dr_list: list[ImpuestoDR]) -> Decimal:
    """
    Determina la tasa de IVA aplicable segun ObjetoImpDR.

    Si ObjetoImpDR es "01", no hay IVA (tasa 0 para control).
    Si ObjetoImpDR es "02", busca la tasa de IVA trasladado en los impuestos DR.
    """
    if objeto_imp_dr == "01":
        return Decimal("0")

    for imp in imp_dr_list:
        if imp.impuesto_dr == "002" and imp.tipo == "traslado":
            return imp.tasa_dr

    # Si ObjetoImpDR es "02" pero no se encuentra tasa, asumir 0.160000
    return Decimal("0.160000")


def _extraer_base_pago(cfdi: CfdiNormalizado) -> list[CfdiClasificado]:
    """
    Extrae la base de ingreso de un CFDI tipo P (complemento de pago).

    Para cada documento relacionado:
    - Si ObjetoImpDR = "02": el monto pagado incluye IVA,
      se divide entre (1 + tasa) para obtener la base.
    - Si ObjetoImpDR = "01": el monto pagado es control, no genera IVA.
    """
    resultados = []

    if cfdi.complemento_pago is None:
        return resultados

    for docto in cfdi.complemento_pago.doctos_relacionados:
        tasa = _tasa_por_objeto_imp_dr(docto.objeto_imp_dr, docto.imp_dr)

        if docto.objeto_imp_dr == "02" and tasa > Decimal("0"):
            # Monto incluye IVA: base = monto / (1 + tasa)
            divisor = Decimal("1") + tasa
            ingreso_base = docto.monto_pagado / divisor
            iva_trasladado = docto.monto_pagado - ingreso_base
        elif docto.objeto_imp_dr == "01":
            # Sin objeto de impuesto: monto es control, no genera IVA
            ingreso_base = docto.monto_pagado
            iva_trasladado = Decimal("0")
        else:
            # ObjetoImpDR = "02" con tasa 0 (exento o tasa 0)
            ingreso_base = docto.monto_pagado
            iva_trasladado = Decimal("0")

        # Extraer retenciones ISR e IVA del documento relacionado
        isr_retenido = Decimal("0")
        iva_retenido = Decimal("0")
        for imp in docto.imp_dr:
            if imp.tipo == "retencion":
                if imp.impuesto_dr == "001":
                    isr_retenido += imp.importe_dr
                elif imp.impuesto_dr == "002":
                    iva_retenido += imp.importe_dr

        clasificado = CfdiClasificado(
            uuid=cfdi.uuid,
            considerado=True,
            motivo=f"Pago complemento, docto {docto.uuid_docto}",
            ingreso_base=ingreso_base,
            iva_trasladado=iva_trasladado,
            iva_retenido=iva_retenido,
            isr_retenido=isr_retenido,
            tasa_iva_aplicada=tasa if docto.objeto_imp_dr == "02" else None,
            es_pago=True,
            trazabilidad=[
                TrazabilidadCfdi(
                    uuid=cfdi.uuid,
                    concepto=f"Pago docto {docto.uuid_docto} (ObjetoImpDR={docto.objeto_imp_dr})",
                    monto=ingreso_base,
                ),
            ],
        )
        resultados.append(clasificado)

    return resultados


def clasificar_cfdi(cfdi: CfdiNormalizado) -> list[CfdiClasificado]:
    """
    Clasifica un CFDI para determinar si debe considerarse en el calculo.

    Reglas:
    - Estado cancelado: excluido
    - Tipo I con PUE: considerado, base desde campo Base de impuestos trasladados
    - Tipo I con PPD: no considerado, espera complemento de pago
    - Tipo P: considerado, monto ajustado segun ObjetoImpDR
    - Tipo E (Egreso): no considerado en iteracion 1
    - Tipo N (Nomina): no considerado para actividades

    Args:
        cfdi: CFDI normalizado a clasificar.

    Returns:
        Lista de CfdiClasificado (puede ser multiple para tipo P con
        varios documentos relacionados).
    """
    # CFDIs cancelados siempre se excluyen
    if cfdi.estado == "cancelado":
        return [
            CfdiClasificado(
                uuid=cfdi.uuid,
                considerado=False,
                motivo="CFDI cancelado",
            )
        ]

    # Tipo I - Ingreso
    if cfdi.tipo == "I":
        if cfdi.metodo_pago == "PUE":
            # PUE: considerado. La base se toma del campo Base de impuestos trasladados
            ingreso_base = Decimal("0")
            iva_trasladado = Decimal("0")
            tasa_iva = cfdi.tasa_iva

            if cfdi.impuestos_trasladados:
                for imp_t in cfdi.impuestos_trasladados:
                    if imp_t.impuesto == "002":  # IVA
                        ingreso_base += imp_t.base
                        iva_trasladado += imp_t.importe
                        if tasa_iva is None:
                            tasa_iva = imp_t.tasa
            else:
                # Sin impuestos trasladados: usar subtotal como base
                ingreso_base = cfdi.subtotal

            # Retenciones ISR e IVA
            isr_retenido = Decimal("0")
            iva_retenido = Decimal("0")
            for imp_r in cfdi.impuestos_retenidos:
                if imp_r.impuesto == "001":
                    isr_retenido += imp_r.importe
                elif imp_r.impuesto == "002":
                    iva_retenido += imp_r.importe

            return [
                CfdiClasificado(
                    uuid=cfdi.uuid,
                    considerado=True,
                    motivo="Ingreso PUE",
                    ingreso_base=ingreso_base,
                    iva_trasladado=iva_trasladado,
                    iva_retenido=iva_retenido,
                    isr_retenido=isr_retenido,
                    tasa_iva_aplicada=tasa_iva,
                    trazabilidad=[
                        TrazabilidadCfdi(
                            uuid=cfdi.uuid,
                            concepto="Ingreso PUE",
                            monto=ingreso_base,
                        ),
                    ],
                )
            ]
        elif cfdi.metodo_pago == "PPD":
            return [
                CfdiClasificado(
                    uuid=cfdi.uuid,
                    considerado=False,
                    motivo="Ingreso PPD: espera complemento de pago",
                )
            ]

    # Tipo P - Pago
    if cfdi.tipo == "P":
        return _extraer_base_pago(cfdi)

    # Tipo E - Egreso (no considerado en iteracion 1)
    if cfdi.tipo == "E":
        return [
            CfdiClasificado(
                uuid=cfdi.uuid,
                considerado=False,
                motivo="Egreso: no considerado en iteracion 1",
            )
        ]

    # Tipo N - Nomina (nunca se mezcla con actividades)
    if cfdi.tipo == "N":
        return [
            CfdiClasificado(
                uuid=cfdi.uuid,
                considerado=False,
                motivo="Nomina: no aplica para calculo de actividades",
            )
        ]

    # Tipo desconocido
    return [
        CfdiClasificado(
            uuid=cfdi.uuid,
            considerado=False,
            motivo=f"Tipo de CFDI no soportado: {cfdi.tipo}",
        )
    ]


def clasificar_cfdis(cfdis: list[CfdiNormalizado]) -> list[CfdiClasificado]:
    """
    Clasifica una lista de CFDIs.

    Args:
        cfdis: Lista de CFDIs normalizados.

    Returns:
        Lista plana de todos los CfdiClasificado.
    """
    resultado = []
    for cfdi in cfdis:
        resultado.extend(clasificar_cfdi(cfdi))
    return resultado
