"""CfdiSource abstraction for fetching / loading CFDI documents."""

from __future__ import annotations

import io
import os
import zipfile
from datetime import date
from typing import Protocol, runtime_checkable

from lxml import etree

from cfdi_parser.ingreso import parse_ingreso
from cfdi_parser.nomina import parse_nomina
from cfdi_parser.pago import parse_pago
from cfdi_parser.retencion import parse_retencion
from cfdi_parser.types import CfdiParseResult

# Namespace URIs for document-type detection
_NS_CFDI4 = "http://www.sat.gob.mx/cfd/4"
_NS_RET = "http://www.sat.gob.mx/esquemas/retencionpago/1"
_NS_PAGO20 = "http://www.sat.gob.mx/Pagos20"
_NS_NOMINA12 = "http://www.sat.gob.mx/nomina12"


@runtime_checkable
class CfdiSource(Protocol):
    """Protocol for any source of CFDI documents."""

    def fetch(
        self,
        rfc: str,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[CfdiParseResult]:
        """Fetch and parse all CFDIs for *rfc* in the given date range."""
        ...


def detect_and_parse(xml_bytes: bytes) -> CfdiParseResult:
    """Auto-detect CFDI type and delegate to the correct parser.

    Detection logic:
    1. If root namespace is retenciones 1.1 -> parse_retencion
    2. If root namespace is CFDI 4.0:
       a. Look for Complemento > Pagos 2.0 namespace -> parse_pago
       b. Look for Complemento > Nomina 1.2 namespace -> parse_nomina
       c. Otherwise -> parse_ingreso (default for I, E, T, N types)
    """
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        return CfdiParseResult(
            tipo="ingreso",
            data=None,  # type: ignore[arg-type]
            errores=[f"XML mal formado: {exc}"],
            es_valido=False,
        )

    tag = root.tag

    # Retenciones 1.1
    if _NS_RET in tag:
        return parse_retencion(xml_bytes)

    # CFDI 4.0 family
    if _NS_CFDI4 in tag:
        # Check for complement namespaces
        nsmap_values = set()
        for elem in root.iter():
            if elem.tag and "{" in elem.tag:
                ns = elem.tag.split("}")[0].lstrip("{")
                nsmap_values.add(ns)

        if _NS_PAGO20 in nsmap_values:
            return parse_pago(xml_bytes)
        if _NS_NOMINA12 in nsmap_values:
            return parse_nomina(xml_bytes)

        # Default: Ingreso (covers TipoDeComprobante I, and others)
        return parse_ingreso(xml_bytes)

    # Unknown namespace
    return CfdiParseResult(
        tipo="ingreso",
        data=None,  # type: ignore[arg-type]
        errores=[f"Tipo de CFDI no reconocido (namespace: {tag})"],
        es_valido=False,
    )


class ManualUploadSource:
    """Source that processes manually uploaded XML or ZIP files.

    Accepts individual XML file bytes or ZIP archives containing
    multiple .xml files. Each XML is auto-detected and parsed.
    """

    def __init__(self, files: list[tuple[str, bytes]]) -> None:
        """Initialize with a list of (filename, content) tuples.

        Args:
            files: List of (filename, raw_bytes) pairs. Files ending
                   in .zip are expanded; .xml files are parsed directly.
        """
        self._files = files

    def fetch(
        self,
        rfc: str,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[CfdiParseResult]:
        """Parse all uploaded files.

        The rfc, fecha_inicio, and fecha_fin parameters are accepted
        for protocol conformance but do not filter the uploaded files.
        All provided files are parsed unconditionally.
        """
        results: list[CfdiParseResult] = []

        for filename, content in self._files:
            lower = filename.lower()

            if lower.endswith(".zip"):
                results.extend(self._process_zip(content))
            elif lower.endswith(".xml"):
                results.append(detect_and_parse(content))
            else:
                results.append(CfdiParseResult(
                    tipo="ingreso",
                    data=None,  # type: ignore[arg-type]
                    errores=[f"Tipo de archivo no soportado: {filename}"],
                    es_valido=False,
                ))

        return results

    @staticmethod
    def _process_zip(zip_bytes: bytes) -> list[CfdiParseResult]:
        """Extract and parse all .xml files from a ZIP archive."""
        results: list[CfdiParseResult] = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".xml"):
                        xml_bytes = zf.read(name)
                        results.append(detect_and_parse(xml_bytes))
        except zipfile.BadZipFile:
            results.append(CfdiParseResult(
                tipo="ingreso",
                data=None,  # type: ignore[arg-type]
                errores=["Archivo ZIP corrupto o invalido"],
                es_valido=False,
            ))
        return results


class PacSource:
    """Placeholder source for PAC (Proveedor Autorizado de Certificacion) download.

    Will be implemented in a future iteration when PAC API integration
    is available.
    """

    def fetch(
        self,
        rfc: str,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[CfdiParseResult]:
        """Not implemented in iteration 1.

        Raises:
            NotImplementedError: Always, with descriptive message.
        """
        raise NotImplementedError(
            "PAC download not available in iteration 1"
        )
