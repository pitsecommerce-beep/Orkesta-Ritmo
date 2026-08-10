"""Parser for CFDI 4.0 Comprobante de Ingreso."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from lxml import etree

from cfdi_parser.types import (
    CfdiIngreso,
    CfdiParseResult,
    Concepto,
    ImpuestoConcepto,
    ImpuestoTotal,
)

NS_CFDI = "http://www.sat.gob.mx/cfd/4"
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"

NSMAP = {
    "cfdi": NS_CFDI,
    "tfd": NS_TFD,
}


def _dec(value: str | None, default: str = "0") -> Decimal:
    """Safely convert a string to Decimal."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(default)


def _str(value: str | None, default: str = "") -> str:
    return value if value is not None else default


def _parse_conceptos(root: etree._Element) -> list[Concepto]:
    """Extract all Concepto nodes and their per-concept taxes."""
    conceptos: list[Concepto] = []
    conceptos_node = root.find("cfdi:Conceptos", NSMAP)
    if conceptos_node is None:
        return conceptos

    for c in conceptos_node.findall("cfdi:Concepto", NSMAP):
        impuestos: list[ImpuestoConcepto] = []

        impuestos_node = c.find("cfdi:Impuestos", NSMAP)
        if impuestos_node is not None:
            # Traslados at concept level
            traslados = impuestos_node.find("cfdi:Traslados", NSMAP)
            if traslados is not None:
                for t in traslados.findall("cfdi:Traslado", NSMAP):
                    impuestos.append(ImpuestoConcepto(
                        base=_dec(t.get("Base")),
                        impuesto=_str(t.get("Impuesto")),
                        tipo_factor=_str(t.get("TipoFactor")),
                        tasa_o_cuota=_dec(t.get("TasaOCuota")),
                        importe=_dec(t.get("Importe")),
                        tipo="traslado",
                    ))
            # Retenciones at concept level
            retenciones = impuestos_node.find("cfdi:Retenciones", NSMAP)
            if retenciones is not None:
                for r in retenciones.findall("cfdi:Retencion", NSMAP):
                    impuestos.append(ImpuestoConcepto(
                        base=_dec(r.get("Base")),
                        impuesto=_str(r.get("Impuesto")),
                        tipo_factor=_str(r.get("TipoFactor")),
                        tasa_o_cuota=_dec(r.get("TasaOCuota")),
                        importe=_dec(r.get("Importe")),
                        tipo="retencion",
                    ))

        conceptos.append(Concepto(
            clave_prod_serv=_str(c.get("ClaveProdServ")),
            cantidad=_dec(c.get("Cantidad")),
            descripcion=_str(c.get("Descripcion")),
            valor_unitario=_dec(c.get("ValorUnitario")),
            importe=_dec(c.get("Importe")),
            objeto_imp=_str(c.get("ObjetoImp")),
            impuestos=impuestos,
        ))
    return conceptos


def _parse_impuestos_totales(
    root: etree._Element,
) -> tuple[list[ImpuestoTotal], list[ImpuestoTotal]]:
    """Extract Impuestos > Traslados and Retenciones totals."""
    trasladados: list[ImpuestoTotal] = []
    retenidos: list[ImpuestoTotal] = []

    impuestos = root.find("cfdi:Impuestos", NSMAP)
    if impuestos is None:
        return trasladados, retenidos

    traslados_node = impuestos.find("cfdi:Traslados", NSMAP)
    if traslados_node is not None:
        for t in traslados_node.findall("cfdi:Traslado", NSMAP):
            trasladados.append(ImpuestoTotal(
                base=_dec(t.get("Base")),
                impuesto=_str(t.get("Impuesto")),
                tipo_factor=_str(t.get("TipoFactor")),
                tasa_o_cuota=_dec(t.get("TasaOCuota")),
                importe=_dec(t.get("Importe")),
            ))

    retenciones_node = impuestos.find("cfdi:Retenciones", NSMAP)
    if retenciones_node is not None:
        for r in retenciones_node.findall("cfdi:Retencion", NSMAP):
            retenidos.append(ImpuestoTotal(
                base=_dec(r.get("Base", "0")),
                impuesto=_str(r.get("Impuesto")),
                tipo_factor=_str(r.get("TipoFactor", "")),
                tasa_o_cuota=_dec(r.get("TasaOCuota", "0")),
                importe=_dec(r.get("Importe")),
            ))

    return trasladados, retenidos


def _extract_uuid(root: etree._Element) -> str:
    """Extract UUID from TimbreFiscalDigital complement."""
    complemento = root.find("cfdi:Complemento", NSMAP)
    if complemento is None:
        return ""
    tfd = complemento.find("tfd:TimbreFiscalDigital", NSMAP)
    if tfd is None:
        return ""
    return _str(tfd.get("UUID")).upper()


def parse_ingreso(xml_bytes: bytes) -> CfdiParseResult:
    """Parse a CFDI 4.0 Ingreso XML document.

    Args:
        xml_bytes: Raw XML content as bytes.

    Returns:
        CfdiParseResult with tipo="ingreso" and data as CfdiIngreso.
    """
    errores: list[str] = []

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return CfdiParseResult(
            tipo="ingreso",
            data=_empty_ingreso(),
            errores=[f"XML mal formado: {exc}"],
            es_valido=False,
        )

    # Verify this is a CFDI 4.0 Ingreso
    version = _str(root.get("Version"))
    tipo_comprobante = _str(root.get("TipoDeComprobante"))
    if version != "4.0":
        errores.append(f"Version inesperada: {version} (se esperaba 4.0)")
    if tipo_comprobante not in ("I", ""):
        errores.append(f"TipoDeComprobante inesperado: {tipo_comprobante} (se esperaba I)")

    # Emisor
    emisor = root.find("cfdi:Emisor", NSMAP)
    rfc_emisor = _str(emisor.get("Rfc")) if emisor is not None else ""
    nombre_emisor = _str(emisor.get("Nombre")) if emisor is not None else ""
    regimen_emisor = _str(emisor.get("RegimenFiscal")) if emisor is not None else ""

    # Receptor
    receptor = root.find("cfdi:Receptor", NSMAP)
    rfc_receptor = _str(receptor.get("Rfc")) if receptor is not None else ""
    nombre_receptor = _str(receptor.get("Nombre")) if receptor is not None else ""
    uso_cfdi = _str(receptor.get("UsoCFDI")) if receptor is not None else ""

    # Conceptos
    conceptos = _parse_conceptos(root)

    # Impuestos totals
    trasladados, retenidos = _parse_impuestos_totales(root)

    # UUID
    uuid = _extract_uuid(root)
    if not uuid:
        errores.append("No se encontro UUID en TimbreFiscalDigital")

    # Parse fecha
    fecha_str = _str(root.get("Fecha"))
    try:
        fecha = datetime.fromisoformat(fecha_str) if fecha_str else datetime.min
    except ValueError:
        fecha = datetime.min
        errores.append(f"Fecha invalida: {fecha_str}")

    ingreso = CfdiIngreso(
        version=version,
        uuid=uuid,
        serie=_str(root.get("Serie")),
        folio=_str(root.get("Folio")),
        fecha=fecha,
        forma_pago=_str(root.get("FormaPago")),
        metodo_pago=_str(root.get("MetodoPago")),
        moneda=_str(root.get("Moneda")),
        tipo_cambio=_dec(root.get("TipoCambio"), "1"),
        subtotal=_dec(root.get("SubTotal")),
        total=_dec(root.get("Total")),
        tipo_comprobante=tipo_comprobante,
        rfc_emisor=rfc_emisor,
        nombre_emisor=nombre_emisor,
        regimen_emisor=regimen_emisor,
        rfc_receptor=rfc_receptor,
        nombre_receptor=nombre_receptor,
        uso_cfdi=uso_cfdi,
        conceptos=conceptos,
        impuestos_trasladados=trasladados,
        impuestos_retenidos=retenidos,
        objeto_imp=_str(root.get("ObjetoImp", "02")),
        estado="vigente",
    )

    return CfdiParseResult(
        tipo="ingreso",
        data=ingreso,
        errores=errores,
        es_valido=len(errores) == 0,
    )


def _empty_ingreso() -> CfdiIngreso:
    """Return an empty CfdiIngreso placeholder for error results."""
    return CfdiIngreso(
        version="",
        uuid="",
        serie="",
        folio="",
        fecha=datetime.min,
        forma_pago="",
        metodo_pago="",
        moneda="",
        tipo_cambio=Decimal("1"),
        subtotal=Decimal("0"),
        total=Decimal("0"),
        tipo_comprobante="",
        rfc_emisor="",
        nombre_emisor="",
        regimen_emisor="",
        rfc_receptor="",
        nombre_receptor="",
        uso_cfdi="",
    )
