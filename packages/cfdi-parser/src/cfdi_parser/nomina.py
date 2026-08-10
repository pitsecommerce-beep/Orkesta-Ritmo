"""Parser for CFDI Nomina 1.2 (payroll)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from lxml import etree

from cfdi_parser.types import (
    CfdiNomina12,
    CfdiParseResult,
    DeduccionDetalle,
    PercepcionDetalle,
)

NS_CFDI = "http://www.sat.gob.mx/cfd/4"
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"
NS_NOMINA = "http://www.sat.gob.mx/nomina12"

NSMAP = {
    "cfdi": NS_CFDI,
    "tfd": NS_TFD,
    "nomina12": NS_NOMINA,
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


def _extract_uuid(root: etree._Element) -> str:
    """Extract UUID from TimbreFiscalDigital."""
    complemento = root.find("cfdi:Complemento", NSMAP)
    if complemento is None:
        return ""
    tfd = complemento.find("tfd:TimbreFiscalDigital", NSMAP)
    if tfd is None:
        return ""
    return _str(tfd.get("UUID")).upper()


def _parse_percepciones(
    nomina_node: etree._Element,
) -> tuple[Decimal, list[PercepcionDetalle]]:
    """Extract Percepciones total and detail."""
    percepciones_node = nomina_node.find("nomina12:Percepciones", NSMAP)
    if percepciones_node is None:
        return Decimal("0"), []

    total_gravado = _dec(percepciones_node.get("TotalGravado"))
    total_exento = _dec(percepciones_node.get("TotalExento"))
    total_sueldos = _dec(percepciones_node.get("TotalSueldos"))
    # Use TotalSueldos if available, otherwise sum gravado + exento
    total = total_sueldos if total_sueldos > 0 else total_gravado + total_exento

    detalle: list[PercepcionDetalle] = []
    for p in percepciones_node.findall("nomina12:Percepcion", NSMAP):
        detalle.append(PercepcionDetalle(
            tipo_percepcion=_str(p.get("TipoPercepcion")),
            clave=_str(p.get("Clave")),
            concepto=_str(p.get("Concepto")),
            importe_gravado=_dec(p.get("ImporteGravado")),
            importe_exento=_dec(p.get("ImporteExento")),
        ))

    return total, detalle


def _parse_deducciones(
    nomina_node: etree._Element,
) -> tuple[Decimal, list[DeduccionDetalle]]:
    """Extract Deducciones total and detail."""
    deducciones_node = nomina_node.find("nomina12:Deducciones", NSMAP)
    if deducciones_node is None:
        return Decimal("0"), []

    total_otras = _dec(deducciones_node.get("TotalOtrasDeducciones"))
    total_impuestos = _dec(deducciones_node.get("TotalImpuestosRetenidos"))
    total = total_otras + total_impuestos

    detalle: list[DeduccionDetalle] = []
    for d in deducciones_node.findall("nomina12:Deduccion", NSMAP):
        detalle.append(DeduccionDetalle(
            tipo_deduccion=_str(d.get("TipoDeduccion")),
            clave=_str(d.get("Clave")),
            concepto=_str(d.get("Concepto")),
            importe=_dec(d.get("Importe")),
        ))

    return total, detalle


def _parse_otros_pagos(nomina_node: etree._Element) -> Decimal:
    """Extract total OtrosPagos."""
    otros = nomina_node.find("nomina12:OtrosPagos", NSMAP)
    if otros is None:
        return Decimal("0")
    total = Decimal("0")
    for op in otros.findall("nomina12:OtroPago", NSMAP):
        total += _dec(op.get("Importe"))
    return total


def parse_nomina(xml_bytes: bytes) -> CfdiParseResult:
    """Parse a CFDI 4.0 with Nomina 1.2 complement.

    Args:
        xml_bytes: Raw XML content as bytes.

    Returns:
        CfdiParseResult with tipo="nomina" and data as CfdiNomina12.
    """
    errores: list[str] = []

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return CfdiParseResult(
            tipo="nomina",
            data=_empty_nomina(),
            errores=[f"XML mal formado: {exc}"],
            es_valido=False,
        )

    # UUID
    uuid = _extract_uuid(root)
    if not uuid:
        errores.append("No se encontro UUID en TimbreFiscalDigital")

    # Emisor
    emisor = root.find("cfdi:Emisor", NSMAP)
    rfc_emisor = _str(emisor.get("Rfc")) if emisor is not None else ""

    # Receptor
    receptor = root.find("cfdi:Receptor", NSMAP)
    rfc_receptor = _str(receptor.get("Rfc")) if receptor is not None else ""
    nombre_receptor = _str(receptor.get("Nombre")) if receptor is not None else ""

    # Fecha
    fecha_str = _str(root.get("Fecha"))
    try:
        fecha = datetime.fromisoformat(fecha_str) if fecha_str else datetime.min
    except ValueError:
        fecha = datetime.min
        errores.append(f"Fecha invalida: {fecha_str}")

    # Find Nomina complement
    complemento = root.find("cfdi:Complemento", NSMAP)
    nomina_node = None
    if complemento is not None:
        nomina_node = complemento.find("nomina12:Nomina", NSMAP)

    if nomina_node is None:
        errores.append("No se encontro complemento Nomina 1.2")
        return CfdiParseResult(
            tipo="nomina",
            data=_empty_nomina(),
            errores=errores,
            es_valido=False,
        )

    version = _str(nomina_node.get("Version"))

    # Percepciones
    total_percepciones, percepciones_detalle = _parse_percepciones(nomina_node)

    # Deducciones
    total_deducciones, deducciones_detalle = _parse_deducciones(nomina_node)

    # Otros pagos
    total_otros_pagos = _parse_otros_pagos(nomina_node)

    nomina = CfdiNomina12(
        version=version,
        uuid=uuid,
        fecha=fecha,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        nombre_receptor=nombre_receptor,
        total_percepciones=total_percepciones,
        total_deducciones=total_deducciones,
        total_otros_pagos=total_otros_pagos,
        percepciones_detalle=percepciones_detalle,
        deducciones_detalle=deducciones_detalle,
    )

    return CfdiParseResult(
        tipo="nomina",
        data=nomina,
        errores=errores,
        es_valido=len(errores) == 0,
    )


def _empty_nomina() -> CfdiNomina12:
    """Return an empty CfdiNomina12 placeholder for error results."""
    return CfdiNomina12(
        version="",
        uuid="",
        fecha=datetime.min,
        rfc_emisor="",
        rfc_receptor="",
        nombre_receptor="",
        total_percepciones=Decimal("0"),
        total_deducciones=Decimal("0"),
        total_otros_pagos=Decimal("0"),
    )
