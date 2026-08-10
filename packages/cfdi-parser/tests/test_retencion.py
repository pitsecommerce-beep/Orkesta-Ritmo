"""Tests for CFDI Retenciones e Informacion de Pagos 1.1 parser."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from cfdi_parser.retencion import parse_retencion
from cfdi_parser.types import CfdiRetencion11


class TestRetencion11:
    """Test parsing CFDI Retenciones 1.1."""

    def test_parse_success(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        assert result.es_valido
        assert result.tipo == "retencion"
        assert len(result.errores) == 0

    def test_uuid(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert data.uuid == "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"

    def test_emisor_receptor(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert data.rfc_emisor == "XAXX010101000"
        assert data.rfc_receptor == "XBXX020202000"

    def test_periodo(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert data.periodo.mes_ini == 1
        assert data.periodo.mes_fin == 6
        assert data.periodo.ejercicio == 2024

    def test_totales(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert data.total_operacion == Decimal("150000.00")
        assert data.total_gravado == Decimal("120000.00")
        assert data.total_exento == Decimal("30000.00")
        assert data.total_retenido == Decimal("18000.00")

    def test_decimal_types(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert isinstance(data.total_operacion, Decimal)
        assert isinstance(data.total_gravado, Decimal)
        assert isinstance(data.total_exento, Decimal)
        assert isinstance(data.total_retenido, Decimal)

    def test_retenciones_detalle(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert len(data.retenciones) == 2

        # ISR retention
        isr = data.retenciones[0]
        assert isr.impuesto == "001"
        assert isr.monto_retenido == Decimal("12000.00")
        assert isr.tipo_pago_ret == "01"

        # IVA retention
        iva = data.retenciones[1]
        assert iva.impuesto == "002"
        assert iva.monto_retenido == Decimal("6000.00")

    def test_complemento_plataformas(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        plat = data.complemento_plataformas
        assert plat is not None
        assert plat.version == "1.0"
        assert plat.periodicidad == "05"
        assert plat.numero_operacion == "PLAT-2024-001"
        assert plat.monto_total_operacion == Decimal("130000.00")
        assert plat.monto_total_retenido == Decimal("12000.00")

    def test_fecha(self, retencion_11_xml: bytes) -> None:
        result = parse_retencion(retencion_11_xml)
        data = result.data
        assert isinstance(data, CfdiRetencion11)
        assert data.fecha == datetime(2024, 6, 30, 23, 59, 59)


class TestRetencion11Errors:
    """Test error handling."""

    def test_malformed_xml(self) -> None:
        result = parse_retencion(b"not xml at all")
        assert not result.es_valido
        assert "XML mal formado" in result.errores[0]

    def test_no_uuid(self) -> None:
        xml = b"""<?xml version="1.0"?>
        <retenciones:Retenciones
            xmlns:retenciones="http://www.sat.gob.mx/esquemas/retencionpago/1"
            Version="1.0" FechaExp="2024-01-01T00:00:00">
            <retenciones:Emisor RFCEmisor="XAXX010101000"/>
            <retenciones:Receptor Nacionalidad="Nacional">
                <retenciones:Nacional RFCRecep="XBXX020202000"/>
            </retenciones:Receptor>
            <retenciones:Periodo MesIni="1" MesFin="1" Ejerc="2024"/>
            <retenciones:Totales montoTotOperacion="1000"
                montoTotGrav="1000" montoTotExent="0" montoTotRet="100"/>
        </retenciones:Retenciones>"""
        result = parse_retencion(xml)
        assert not result.es_valido
        assert any("UUID" in e for e in result.errores)
