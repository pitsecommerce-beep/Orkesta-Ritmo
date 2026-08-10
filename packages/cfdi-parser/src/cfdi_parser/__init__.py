"""cfdi_parser -- CFDI 4.0 XML parser for Orkesta Ritmo.

Parses Mexican fiscal digital invoices (CFDI) into typed Python dataclasses
with Decimal precision for all monetary values.
"""

from cfdi_parser.types import (
    CfdiIngreso,
    CfdiNomina12,
    CfdiParseResult,
    CfdiRetencion11,
    ComplementoPago20,
    Concepto,
    DoctoRelacionado,
    ImpuestoConcepto,
    ImpuestoDR,
    ImpuestoTotal,
    Pago20,
    TotalesPago20,
)
from cfdi_parser.ingreso import parse_ingreso
from cfdi_parser.pago import parse_pago
from cfdi_parser.nomina import parse_nomina
from cfdi_parser.retencion import parse_retencion
from cfdi_parser.source import CfdiSource, ManualUploadSource, PacSource
from cfdi_parser.validator import validate_cfdi_xml

__all__ = [
    # Types
    "CfdiIngreso",
    "CfdiNomina12",
    "CfdiParseResult",
    "CfdiRetencion11",
    "ComplementoPago20",
    "Concepto",
    "DoctoRelacionado",
    "ImpuestoConcepto",
    "ImpuestoDR",
    "ImpuestoTotal",
    "Pago20",
    "TotalesPago20",
    # Parsers
    "parse_ingreso",
    "parse_pago",
    "parse_nomina",
    "parse_retencion",
    # Sources
    "CfdiSource",
    "ManualUploadSource",
    "PacSource",
    # Validation
    "validate_cfdi_xml",
]
