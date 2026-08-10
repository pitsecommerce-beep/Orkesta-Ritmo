"""Tests for CFDI Ingreso 4.0 parser."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from cfdi_parser.ingreso import parse_ingreso
from cfdi_parser.types import CfdiIngreso
from cfdi_parser.validator import validate_cfdi_xml


class TestIngresoPUE:
    """Test parsing a PUE (Pago en Una sola Exhibicion) invoice."""

    def test_parse_success(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        assert result.es_valido
        assert result.tipo == "ingreso"
        assert len(result.errores) == 0

    def test_basic_fields(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.version == "4.0"
        assert data.serie == "A"
        assert data.folio == "12345"
        assert data.tipo_comprobante == "I"
        assert data.metodo_pago == "PUE"
        assert data.forma_pago == "01"
        assert data.moneda == "MXN"

    def test_uuid_extraction(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.uuid == "6A8B9C0D-1E2F-3A4B-5C6D-7E8F9A0B1C2D"

    def test_decimal_values(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        # Verify exact Decimal types, not float
        assert isinstance(data.subtotal, Decimal)
        assert isinstance(data.total, Decimal)
        assert isinstance(data.tipo_cambio, Decimal)
        assert data.subtotal == Decimal("10000.00")
        assert data.total == Decimal("11600.00")
        assert data.tipo_cambio == Decimal("1")

    def test_emisor(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.rfc_emisor == "XAXX010101000"
        assert data.nombre_emisor == "EMPRESA SINTETICA SA DE CV"
        assert data.regimen_emisor == "601"

    def test_receptor(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.rfc_receptor == "XBXX020202000"
        assert data.nombre_receptor == "CLIENTE SINTETICO PERSONA FISICA"
        assert data.uso_cfdi == "G03"

    def test_conceptos(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert len(data.conceptos) == 1
        concepto = data.conceptos[0]
        assert concepto.clave_prod_serv == "84111506"
        assert concepto.cantidad == Decimal("1")
        assert concepto.descripcion == "Servicios de consultoria en tecnologia"
        assert concepto.valor_unitario == Decimal("10000.00")
        assert concepto.importe == Decimal("10000.00")
        assert concepto.objeto_imp == "02"

    def test_concepto_taxes(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        concepto = data.conceptos[0]
        assert len(concepto.impuestos) == 1
        tax = concepto.impuestos[0]
        assert tax.impuesto == "002"  # IVA
        assert tax.tipo_factor == "Tasa"
        assert tax.tasa_o_cuota == Decimal("0.160000")
        assert tax.importe == Decimal("1600.00")
        assert tax.tipo == "traslado"

    def test_impuestos_totales(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert len(data.impuestos_trasladados) == 1
        traslado = data.impuestos_trasladados[0]
        assert traslado.impuesto == "002"
        assert traslado.importe == Decimal("1600.00")
        assert len(data.impuestos_retenidos) == 0

    def test_fecha(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.fecha == datetime(2024, 3, 15, 10, 30, 0)

    def test_estado_default(self, ingreso_pue_xml: bytes) -> None:
        result = parse_ingreso(ingreso_pue_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.estado == "vigente"

    def test_validation_passes(self, ingreso_pue_xml: bytes) -> None:
        errors = validate_cfdi_xml(ingreso_pue_xml)
        assert errors == []


class TestIngresoPPD:
    """Test parsing a PPD (Pago en Parcialidades o Diferido) invoice."""

    def test_ppd_fields(self, ingreso_ppd_xml: bytes) -> None:
        result = parse_ingreso(ingreso_ppd_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.metodo_pago == "PPD"
        assert data.forma_pago == "99"
        assert data.moneda == "USD"
        assert data.tipo_cambio == Decimal("17.1523")
        assert data.uuid == "1A2B3C4D-5E6F-7A8B-9C0D-1E2F3A4B5C6D"

    def test_ppd_amounts(self, ingreso_ppd_xml: bytes) -> None:
        result = parse_ingreso(ingreso_ppd_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        assert data.subtotal == Decimal("5000.00")
        assert data.total == Decimal("5800.00")

    def test_ppd_multiple_quantities(self, ingreso_ppd_xml: bytes) -> None:
        result = parse_ingreso(ingreso_ppd_xml)
        data = result.data
        assert isinstance(data, CfdiIngreso)
        concepto = data.conceptos[0]
        assert concepto.cantidad == Decimal("10")
        assert concepto.valor_unitario == Decimal("500.00")


class TestIngresoErrors:
    """Test error handling for invalid XML."""

    def test_malformed_xml(self) -> None:
        result = parse_ingreso(b"<not valid xml")
        assert not result.es_valido
        assert len(result.errores) > 0
        assert "XML mal formado" in result.errores[0]

    def test_empty_bytes(self) -> None:
        result = parse_ingreso(b"")
        assert not result.es_valido

    def test_no_uuid(self) -> None:
        xml = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
            Version="4.0" TipoDeComprobante="I"
            SubTotal="100" Total="116" Moneda="MXN">
            <cfdi:Emisor Rfc="XAXX010101000" Nombre="TEST" RegimenFiscal="601"/>
            <cfdi:Receptor Rfc="XBXX020202000" Nombre="TEST" UsoCFDI="G03"/>
        </cfdi:Comprobante>"""
        result = parse_ingreso(xml)
        assert not result.es_valido
        assert any("UUID" in e for e in result.errores)
