"""Tests for CFDI Nomina 1.2 parser."""

from __future__ import annotations

import io
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from cfdi_parser.nomina import parse_nomina
from cfdi_parser.source import ManualUploadSource, PacSource, detect_and_parse
from cfdi_parser.types import CfdiIngreso, CfdiNomina12, ComplementoPago20
from cfdi_parser.validator import validate_rfc, validate_uuid

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestNomina12:
    """Test parsing CFDI Nomina 1.2."""

    def test_parse_success(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        assert result.es_valido
        assert result.tipo == "nomina"
        assert len(result.errores) == 0

    def test_uuid(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert data.uuid == "FADE1234-5678-9ABC-DEF0-123456789ABC"

    def test_version(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert data.version == "1.2"

    def test_emisor_receptor(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert data.rfc_emisor == "XAXX010101000"
        assert data.rfc_receptor == "XBXX020202000"
        assert data.nombre_receptor == "EMPLEADO SINTETICO GARCIA LOPEZ"

    def test_totales(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert data.total_percepciones == Decimal("15000.00")
        assert data.total_deducciones == Decimal("3500.00")
        assert data.total_otros_pagos == Decimal("700.00")

    def test_decimal_types(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert isinstance(data.total_percepciones, Decimal)
        assert isinstance(data.total_deducciones, Decimal)
        assert isinstance(data.total_otros_pagos, Decimal)

    def test_percepciones_detalle(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert len(data.percepciones_detalle) == 2

        sueldo = data.percepciones_detalle[0]
        assert sueldo.tipo_percepcion == "001"
        assert sueldo.concepto == "Sueldo"
        assert sueldo.importe_gravado == Decimal("10000.00")
        assert sueldo.importe_exento == Decimal("0.00")

        ahorro = data.percepciones_detalle[1]
        assert ahorro.tipo_percepcion == "005"
        assert ahorro.concepto == "Fondo de ahorro"
        assert ahorro.importe_gravado == Decimal("2000.00")
        assert ahorro.importe_exento == Decimal("3000.00")

    def test_deducciones_detalle(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert len(data.deducciones_detalle) == 2

        isr = data.deducciones_detalle[0]
        assert isr.tipo_deduccion == "002"
        assert isr.concepto == "ISR"
        assert isr.importe == Decimal("2000.00")

        imss = data.deducciones_detalle[1]
        assert imss.tipo_deduccion == "001"
        assert imss.concepto == "Seguridad social"
        assert imss.importe == Decimal("1500.00")

    def test_fecha(self, nomina_12_xml: bytes) -> None:
        result = parse_nomina(nomina_12_xml)
        data = result.data
        assert isinstance(data, CfdiNomina12)
        assert data.fecha == datetime(2024, 1, 31, 12, 0, 0)


class TestNomina12Errors:
    """Test error handling."""

    def test_malformed_xml(self) -> None:
        result = parse_nomina(b"broken xml {{")
        assert not result.es_valido
        assert "XML mal formado" in result.errores[0]

    def test_no_nomina_complement(self) -> None:
        xml = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
            Version="4.0" TipoDeComprobante="N"
            SubTotal="1000" Total="1000" Moneda="MXN">
            <cfdi:Emisor Rfc="XAXX010101000" Nombre="TEST" RegimenFiscal="601"/>
            <cfdi:Receptor Rfc="XBXX020202000" Nombre="TEST" UsoCFDI="CN01"/>
            <cfdi:Complemento/>
        </cfdi:Comprobante>"""
        result = parse_nomina(xml)
        assert not result.es_valido
        assert any("Nomina 1.2" in e for e in result.errores)


class TestManualUploadSource:
    """Test ManualUploadSource with XML and ZIP files."""

    def test_single_xml(self, ingreso_pue_xml: bytes) -> None:
        source = ManualUploadSource([("factura.xml", ingreso_pue_xml)])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert results[0].es_valido
        assert results[0].tipo == "ingreso"

    def test_multiple_xml(
        self, ingreso_pue_xml: bytes, nomina_12_xml: bytes
    ) -> None:
        source = ManualUploadSource([
            ("factura.xml", ingreso_pue_xml),
            ("nomina.xml", nomina_12_xml),
        ])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 2
        assert results[0].tipo == "ingreso"
        assert results[1].tipo == "nomina"

    def test_zip_file(self, ingreso_pue_xml: bytes, pago_20_xml: bytes) -> None:
        # Create a ZIP in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("factura.xml", ingreso_pue_xml)
            zf.writestr("pago.xml", pago_20_xml)
        zip_bytes = buf.getvalue()

        source = ManualUploadSource([("cfdis.zip", zip_bytes)])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 2
        tipos = {r.tipo for r in results}
        assert "ingreso" in tipos
        assert "pago" in tipos

    def test_unsupported_file(self) -> None:
        source = ManualUploadSource([("data.csv", b"col1,col2\n1,2")])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert not results[0].es_valido
        assert "no soportado" in results[0].errores[0]

    def test_bad_zip(self) -> None:
        source = ManualUploadSource([("bad.zip", b"not a zip file")])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert not results[0].es_valido
        assert "ZIP" in results[0].errores[0]


class TestPacSource:
    """Test PacSource placeholder."""

    def test_raises_not_implemented(self) -> None:
        source = PacSource()
        with pytest.raises(NotImplementedError, match="PAC download not available in iteration 1"):
            source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))


class TestAutoDetect:
    """Test detect_and_parse auto-detection."""

    def test_detect_ingreso(self, ingreso_pue_xml: bytes) -> None:
        result = detect_and_parse(ingreso_pue_xml)
        assert result.tipo == "ingreso"
        assert result.es_valido

    def test_detect_pago(self, pago_20_xml: bytes) -> None:
        result = detect_and_parse(pago_20_xml)
        assert result.tipo == "pago"
        assert result.es_valido

    def test_detect_nomina(self, nomina_12_xml: bytes) -> None:
        result = detect_and_parse(nomina_12_xml)
        assert result.tipo == "nomina"
        assert result.es_valido

    def test_detect_retencion(self, retencion_11_xml: bytes) -> None:
        result = detect_and_parse(retencion_11_xml)
        assert result.tipo == "retencion"
        assert result.es_valido


class TestValidator:
    """Test standalone validator functions."""

    def test_valid_uuid(self) -> None:
        errors = validate_uuid("6A8B9C0D-1E2F-3A4B-5C6D-7E8F9A0B1C2D")
        assert errors == []

    def test_invalid_uuid(self) -> None:
        errors = validate_uuid("not-a-uuid")
        assert len(errors) == 1

    def test_empty_uuid(self) -> None:
        errors = validate_uuid("")
        assert len(errors) == 1

    def test_valid_rfc_pf(self) -> None:
        errors = validate_rfc("XAXX010101000")
        assert errors == []

    def test_valid_rfc_pm(self) -> None:
        errors = validate_rfc("XAX010101000")
        assert errors == []

    def test_invalid_rfc_length(self) -> None:
        errors = validate_rfc("SHORT")
        assert len(errors) == 1
        assert "longitud" in errors[0]

    def test_invalid_rfc_format(self) -> None:
        errors = validate_rfc("1234567890123")
        assert len(errors) == 1
        assert "formato" in errors[0]
