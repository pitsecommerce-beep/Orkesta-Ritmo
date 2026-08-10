"""Parser for CFDI Retenciones e Informacion de Pagos 1.1."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from lxml import etree

from cfdi_parser.types import (
    CfdiParseResult,
    CfdiRetencion11,
    ComplementoPlataformas,
    PeriodoRetencion,
    RetencionDetalle,
)

NS_RET = "http://www.sat.gob.mx/esquemas/retencionpago/1"
NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"
NS_PLATAFORMAS = "http://www.sat.gob.mx/esquemas/retencionpago/1/PlataformasTecnologicas10"

NSMAP = {
    "ret": NS_RET,
    "tfd": NS_TFD,
    "plat": NS_PLATAFORMAS,
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


def _extract_uuid(root: etree._Element) -> str:
    """Extract UUID from TimbreFiscalDigital within Complemento."""
    complemento = root.find("ret:Complemento", NSMAP)
    if complemento is None:
        return ""
    tfd = complemento.find("tfd:TimbreFiscalDigital", NSMAP)
    if tfd is None:
        return ""
    return _str(tfd.get("UUID")).upper()


def _parse_periodo(root: etree._Element) -> PeriodoRetencion:
    """Extract Periodo node."""
    periodo = root.find("ret:Periodo", NSMAP)
    if periodo is None:
        return PeriodoRetencion(mes_ini=0, mes_fin=0, ejercicio=0)
    return PeriodoRetencion(
        mes_ini=_int(periodo.get("MesIni")),
        mes_fin=_int(periodo.get("MesFin")),
        ejercicio=_int(periodo.get("Ejerc")),
    )


def _parse_retenciones(root: etree._Element) -> list[RetencionDetalle]:
    """Extract Retenciones detail."""
    result: list[RetencionDetalle] = []
    totales = root.find("ret:Totales", NSMAP)
    if totales is None:
        return result

    # In CFDI Retenciones 1.1, individual tax lines are under
    # ImpRetenidos nodes inside Totales
    for imp in totales.findall("ret:ImpRetenidos", NSMAP):
        result.append(RetencionDetalle(
            impuesto=_str(imp.get("Impuesto")),
            monto_retenido=_dec(imp.get("montoRet")),
            tipo_pago_ret=_str(imp.get("TipoPagoRet")),
        ))

    return result


def _parse_plataformas(root: etree._Element) -> ComplementoPlataformas | None:
    """Extract optional Complemento de Servicios Plataformas Tecnologicas."""
    complemento = root.find("ret:Complemento", NSMAP)
    if complemento is None:
        return None
    plat = complemento.find("plat:ServiciosPlataformasTecnologicas", NSMAP)
    if plat is None:
        return None
    return ComplementoPlataformas(
        version=_str(plat.get("Version")),
        periodicidad=_str(plat.get("Periodicidad")),
        numero_operacion=_str(plat.get("NumServ")),
        monto_total_operacion=_dec(plat.get("MonTotServSIVA")),
        monto_total_retenido=_dec(plat.get("TotalISRRetenido")),
    )


def _parse_totales(root: etree._Element) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Extract total amounts from Totales node.

    Returns:
        (total_operacion, total_gravado, total_exento, total_retenido)
    """
    totales = root.find("ret:Totales", NSMAP)
    if totales is None:
        return Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
    return (
        _dec(totales.get("montoTotOperacion")),
        _dec(totales.get("montoTotGrav")),
        _dec(totales.get("montoTotExworked")),
        _dec(totales.get("montoTotRet")),
    )


def parse_retencion(xml_bytes: bytes) -> CfdiParseResult:
    """Parse a CFDI Retenciones e Informacion de Pagos 1.1.

    Args:
        xml_bytes: Raw XML content as bytes.

    Returns:
        CfdiParseResult with tipo="retencion" and data as CfdiRetencion11.
    """
    errores: list[str] = []

    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return CfdiParseResult(
            tipo="retencion",
            data=_empty_retencion(),
            errores=[f"XML mal formado: {exc}"],
            es_valido=False,
        )

    version = _str(root.get("Version"))

    # Emisor
    emisor = root.find("ret:Emisor", NSMAP)
    rfc_emisor = _str(emisor.get("RFCEmisor")) if emisor is not None else ""

    # Receptor
    receptor = root.find("ret:Receptor", NSMAP)
    rfc_receptor = ""
    if receptor is not None:
        # Receptor > Nacional
        nacional = receptor.find("ret:Nacional", NSMAP)
        if nacional is not None:
            rfc_receptor = _str(nacional.get("RFCRecep"))
        else:
            rfc_receptor = _str(receptor.get("RFCRecep"))

    # UUID
    uuid = _extract_uuid(root)
    if not uuid:
        errores.append("No se encontro UUID en TimbreFiscalDigital")

    # Fecha
    fecha_str = _str(root.get("FechaExp"))
    try:
        fecha = datetime.fromisoformat(fecha_str) if fecha_str else datetime.min
    except ValueError:
        fecha = datetime.min
        errores.append(f"Fecha invalida: {fecha_str}")

    # Periodo
    periodo = _parse_periodo(root)

    # Totales
    totales_node = root.find("ret:Totales", NSMAP)
    total_operacion = Decimal("0")
    total_gravado = Decimal("0")
    total_exento = Decimal("0")
    total_retenido = Decimal("0")
    if totales_node is not None:
        total_operacion = _dec(totales_node.get("montoTotOperacion"))
        total_gravado = _dec(totales_node.get("montoTotGrav"))
        total_exento = _dec(totales_node.get("montoTotExent"))
        total_retenido = _dec(totales_node.get("montoTotRet"))

    # Retenciones
    retenciones = _parse_retenciones(root)

    # Plataformas
    plataformas = _parse_plataformas(root)

    retencion = CfdiRetencion11(
        version=version,
        uuid=uuid,
        fecha=fecha,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        periodo=periodo,
        total_operacion=total_operacion,
        total_gravado=total_gravado,
        total_exento=total_exento,
        total_retenido=total_retenido,
        retenciones=retenciones,
        complemento_plataformas=plataformas,
    )

    return CfdiParseResult(
        tipo="retencion",
        data=retencion,
        errores=errores,
        es_valido=len(errores) == 0,
    )


def _empty_retencion() -> CfdiRetencion11:
    """Return an empty CfdiRetencion11 placeholder for error results."""
    return CfdiRetencion11(
        version="",
        uuid="",
        fecha=datetime.min,
        rfc_emisor="",
        rfc_receptor="",
        periodo=PeriodoRetencion(mes_ini=0, mes_fin=0, ejercicio=0),
        total_operacion=Decimal("0"),
        total_gravado=Decimal("0"),
        total_exento=Decimal("0"),
        total_retenido=Decimal("0"),
    )
