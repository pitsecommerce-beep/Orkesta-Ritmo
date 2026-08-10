"""Parser for Complemento de Pago 2.0."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from lxml import etree

from cfdi_parser.types import (
    CfdiParseResult,
    ComplementoPago20,
    DoctoRelacionado,
    ImpuestoDR,
    Pago20,
    TotalesPago20,
)

NS_CFDI = "http://www.sat.gob.mx/cfd/4"
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"
NS_PAGO20 = "http://www.sat.gob.mx/Pagos20"

NSMAP = {
    "cfdi": NS_CFDI,
    "tfd": NS_TFD,
    "pago20": NS_PAGO20,
}


def _dec(value: str | None, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(default)


def _str(value: str | None, default: str = "") -> str:
    return value if value is not None else default


def _int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_totales(pagos_node: etree._Element) -> TotalesPago20 | None:
    """Extract optional Totales node."""
    totales = pagos_node.find("pago20:Totales", NSMAP)
    if totales is None:
        return None
    return TotalesPago20(
        total_retenciones_iva=_dec(totales.get("TotalRetencionesIVA")),
        total_retenciones_isr=_dec(totales.get("TotalRetencionesISR")),
        total_retenciones_ieps=_dec(totales.get("TotalRetencionesIEPS")),
        total_traslados_base_iva16=_dec(totales.get("TotalTrasladosBaseIVA16")),
        total_traslados_impuesto_iva16=_dec(totales.get("TotalTrasladosImpuestoIVA16")),
        total_traslados_base_iva8=_dec(totales.get("TotalTrasladosBaseIVA8")),
        total_traslados_impuesto_iva8=_dec(totales.get("TotalTrasladosImpuestoIVA8")),
        total_traslados_base_iva0=_dec(totales.get("TotalTrasladosBaseIVA0")),
        total_traslados_impuesto_iva0=_dec(totales.get("TotalTrasladosImpuestoIVA0")),
        total_traslados_base_iva_exento=_dec(totales.get("TotalTrasladosBaseIVAExento")),
        monto_total_pagos=_dec(totales.get("MontoTotalPagos")),
    )


def _parse_impuestos_dr(
    docto: etree._Element,
) -> list[ImpuestoDR]:
    """Extract ImpuestosDR from a DoctoRelacionado node."""
    result: list[ImpuestoDR] = []

    impuestos_node = docto.find("pago20:ImpuestosDR", NSMAP)
    if impuestos_node is None:
        return result

    # Traslados DR
    traslados = impuestos_node.find("pago20:TrasladosDR", NSMAP)
    if traslados is not None:
        for t in traslados.findall("pago20:TrasladoDR", NSMAP):
            result.append(ImpuestoDR(
                base_dr=_dec(t.get("BaseDR")),
                impuesto_dr=_str(t.get("ImpuestoDR")),
                tipo_factor_dr=_str(t.get("TipoFactorDR")),
                tasa_o_cuota_dr=_dec(t.get("TasaOCuotaDR")),
                importe_dr=_dec(t.get("ImporteDR")),
                tipo="traslado",
            ))

    # Retenciones DR
    retenciones = impuestos_node.find("pago20:RetencionesDR", NSMAP)
    if retenciones is not None:
        for r in retenciones.findall("pago20:RetencionDR", NSMAP):
            result.append(ImpuestoDR(
                base_dr=_dec(r.get("BaseDR")),
                impuesto_dr=_str(r.get("ImpuestoDR")),
                tipo_factor_dr=_str(r.get("TipoFactorDR")),
                tasa_o_cuota_dr=_dec(r.get("TasaOCuotaDR")),
                importe_dr=_dec(r.get("ImporteDR")),
                tipo="retencion",
            ))

    return result


def _parse_doctos(pago_node: etree._Element) -> list[DoctoRelacionado]:
    """Extract all DoctoRelacionado from a Pago node."""
    doctos: list[DoctoRelacionado] = []
    for d in pago_node.findall("pago20:DoctoRelacionado", NSMAP):
        doctos.append(DoctoRelacionado(
            id_documento=_str(d.get("IdDocumento")).upper(),
            serie=_str(d.get("Serie")),
            folio=_str(d.get("Folio")),
            moneda=_str(d.get("MonedaDR")),
            equivalencia=_dec(d.get("EquivalenciaDR"), "1"),
            num_parcialidad=_int(d.get("NumParcialidad"), 1),
            imp_saldo_ant=_dec(d.get("ImpSaldoAnt")),
            imp_pagado=_dec(d.get("ImpPagado")),
            imp_saldo_insoluto=_dec(d.get("ImpSaldoInsoluto")),
            objeto_imp_dr=_str(d.get("ObjetoImpDR")),
            impuestos_dr=_parse_impuestos_dr(d),
        ))
    return doctos


def parse_pago(xml_bytes: bytes) -> CfdiParseResult:
    """Parse a CFDI 4.0 with Complemento de Pago 2.0.

    Args:
        xml_bytes: Raw XML content as bytes.

    Returns:
        CfdiParseResult with tipo="pago" and data as ComplementoPago20.
    """
    errores: list[str] = []

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return CfdiParseResult(
            tipo="pago",
            data=ComplementoPago20(version="", totales=None, pagos=[]),
            errores=[f"XML mal formado: {exc}"],
            es_valido=False,
        )

    # Navigate to Complemento > Pagos
    complemento = root.find("cfdi:Complemento", NSMAP)
    if complemento is None:
        errores.append("No se encontro nodo Complemento")
        return CfdiParseResult(
            tipo="pago",
            data=ComplementoPago20(version="", totales=None, pagos=[]),
            errores=errores,
            es_valido=False,
        )

    pagos_node = complemento.find("pago20:Pagos", NSMAP)
    if pagos_node is None:
        errores.append("No se encontro nodo Pagos 2.0")
        return CfdiParseResult(
            tipo="pago",
            data=ComplementoPago20(version="", totales=None, pagos=[]),
            errores=errores,
            es_valido=False,
        )

    version = _str(pagos_node.get("Version"))
    totales = _parse_totales(pagos_node)

    pagos: list[Pago20] = []
    for p in pagos_node.findall("pago20:Pago", NSMAP):
        fecha_str = _str(p.get("FechaPago"))
        try:
            fecha_pago = datetime.fromisoformat(fecha_str) if fecha_str else datetime.min
        except ValueError:
            fecha_pago = datetime.min
            errores.append(f"FechaPago invalida: {fecha_str}")

        pagos.append(Pago20(
            fecha_pago=fecha_pago,
            forma_pago=_str(p.get("FormaDePagoP")),
            monto=_dec(p.get("Monto")),
            moneda=_str(p.get("MonedaP")),
            tipo_cambio=_dec(p.get("TipoCambioP"), "1"),
            doctos_relacionados=_parse_doctos(p),
        ))

    complemento_pago = ComplementoPago20(
        version=version,
        totales=totales,
        pagos=pagos,
    )

    return CfdiParseResult(
        tipo="pago",
        data=complemento_pago,
        errores=errores,
        es_valido=len(errores) == 0,
    )
