"""Basic validation for CFDI XML documents at ingestion time."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from lxml import etree

# UUID v4 pattern (case-insensitive, SAT uses uppercase)
_UUID_RE = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)

# RFC patterns:
#   Persona Moral (PM): 3 letters + 6 digits + 3 alphanumeric = 12 chars
#   Persona Fisica (PF): 4 letters + 6 digits + 3 alphanumeric = 13 chars
#   Generic / foreign: XAXX010101000 (13), XEXX010101000 (13)
_RFC_RE = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$")


def validate_uuid(uuid: str) -> list[str]:
    """Validate a UUID string.

    Returns:
        List of error messages (empty if valid).
    """
    if not uuid:
        return ["UUID vacio"]
    if not _UUID_RE.match(uuid):
        return [f"UUID con formato invalido: {uuid}"]
    return []


def validate_rfc(rfc: str, campo: str = "RFC") -> list[str]:
    """Validate an RFC string.

    Args:
        rfc: The RFC to validate.
        campo: Field name for error messages.

    Returns:
        List of error messages (empty if valid).
    """
    if not rfc:
        return [f"{campo} vacio"]
    if len(rfc) not in (12, 13):
        return [f"{campo} con longitud invalida: {len(rfc)} (se esperaba 12 o 13)"]
    if not _RFC_RE.match(rfc):
        return [f"{campo} con formato invalido: {rfc}"]
    return []


def validate_amount(value_str: str | None, campo: str = "Monto") -> list[str]:
    """Validate that a string can be parsed as a non-negative Decimal.

    Returns:
        List of error messages (empty if valid).
    """
    if value_str is None:
        return []
    try:
        val = Decimal(value_str)
    except InvalidOperation:
        return [f"{campo} no es un numero valido: {value_str}"]
    if val < 0:
        return [f"{campo} es negativo: {value_str}"]
    return []


def validate_amounts_consistent(
    subtotal_str: str | None,
    total_str: str | None,
    impuestos_traslados_str: str | None,
    impuestos_retenidos_str: str | None,
) -> list[str]:
    """Check that total ~ subtotal + traslados - retenidos.

    Allows a tolerance of 0.01 MXN due to rounding.

    Returns:
        List of error messages (empty if consistent).
    """
    try:
        subtotal = Decimal(subtotal_str or "0")
        total = Decimal(total_str or "0")
        traslados = Decimal(impuestos_traslados_str or "0")
        retenidos = Decimal(impuestos_retenidos_str or "0")
    except InvalidOperation:
        return []  # Malformed amounts are caught by validate_amount

    expected = subtotal + traslados - retenidos
    diff = abs(total - expected)
    if diff > Decimal("0.01"):
        return [
            f"Inconsistencia en montos: Total={total}, "
            f"esperado (SubTotal + Traslados - Retenciones) = {expected}, "
            f"diferencia={diff}"
        ]
    return []


def validate_cfdi_xml(xml_bytes: bytes) -> list[str]:
    """Run basic validation checks on raw CFDI XML.

    Checks performed:
    1. Well-formed XML
    2. Required root attributes (Version, Total, SubTotal)
    3. UUID format (if TimbreFiscalDigital present)
    4. RFC format for Emisor and Receptor
    5. Amount consistency (Total vs SubTotal + taxes)

    Args:
        xml_bytes: Raw XML content as bytes.

    Returns:
        List of error messages (empty if all checks pass).
    """
    errores: list[str] = []

    # 1. Well-formed XML
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return [f"XML mal formado: {exc}"]

    # Detect document type by namespace
    tag = root.tag
    ns_cfdi4 = "http://www.sat.gob.mx/cfd/4"
    ns_ret = "http://www.sat.gob.mx/esquemas/retencionpago/1"

    if ns_ret in tag:
        # Retenciones document -- different structure
        return _validate_retencion(root)

    if ns_cfdi4 not in tag:
        errores.append(f"Namespace raiz inesperado: {tag}")
        return errores

    # 2. Required attributes
    nsmap = {"cfdi": ns_cfdi4, "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"}

    version = root.get("Version")
    if not version:
        errores.append("Atributo Version ausente")

    subtotal_str = root.get("SubTotal")
    if subtotal_str is None:
        errores.append("Atributo SubTotal ausente")
    else:
        errores.extend(validate_amount(subtotal_str, "SubTotal"))

    total_str = root.get("Total")
    if total_str is None:
        errores.append("Atributo Total ausente")
    else:
        errores.extend(validate_amount(total_str, "Total"))

    # 3. UUID
    complemento = root.find("cfdi:Complemento", nsmap)
    if complemento is not None:
        tfd = complemento.find("tfd:TimbreFiscalDigital", nsmap)
        if tfd is not None:
            uuid = tfd.get("UUID", "")
            errores.extend(validate_uuid(uuid))

    # 4. RFC
    emisor = root.find("cfdi:Emisor", nsmap)
    if emisor is not None:
        rfc_emisor = emisor.get("Rfc", "")
        errores.extend(validate_rfc(rfc_emisor, "RFC Emisor"))
    else:
        errores.append("Nodo Emisor ausente")

    receptor = root.find("cfdi:Receptor", nsmap)
    if receptor is not None:
        rfc_receptor = receptor.get("Rfc", "")
        errores.extend(validate_rfc(rfc_receptor, "RFC Receptor"))
    else:
        errores.append("Nodo Receptor ausente")

    # 5. Amount consistency
    impuestos = root.find("cfdi:Impuestos", nsmap)
    traslados_total = None
    retenidos_total = None
    if impuestos is not None:
        traslados_total = impuestos.get("TotalImpuestosTrasladados")
        retenidos_total = impuestos.get("TotalImpuestosRetenidos")

    errores.extend(validate_amounts_consistent(
        subtotal_str, total_str, traslados_total, retenidos_total,
    ))

    return errores


def _validate_retencion(root: etree._Element) -> list[str]:
    """Validate a Retenciones 1.1 document (simplified checks)."""
    errores: list[str] = []
    nsmap = {
        "ret": "http://www.sat.gob.mx/esquemas/retencionpago/1",
        "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
    }

    version = root.get("Version")
    if not version:
        errores.append("Atributo Version ausente")

    # UUID
    complemento = root.find("ret:Complemento", nsmap)
    if complemento is not None:
        tfd = complemento.find("tfd:TimbreFiscalDigital", nsmap)
        if tfd is not None:
            uuid = tfd.get("UUID", "")
            errores.extend(validate_uuid(uuid))

    # Emisor RFC
    emisor = root.find("ret:Emisor", nsmap)
    if emisor is not None:
        rfc = emisor.get("RFCEmisor", "")
        errores.extend(validate_rfc(rfc, "RFC Emisor"))

    return errores
