"""Tests for Complemento de Pago 2.0 parser."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from cfdi_parser.pago import parse_pago
from cfdi_parser.types import ComplementoPago20


class TestPago20:
    """Test parsing Complemento de Pago 2.0."""

    def test_parse_success(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        assert result.es_valido
        assert result.tipo == "pago"
        assert len(result.errores) == 0

    def test_version(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        assert data.version == "2.0"

    def test_totales(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        assert data.totales is not None
        totales = data.totales
        assert isinstance(totales.monto_total_pagos, Decimal)
        assert totales.monto_total_pagos == Decimal("29000.00")
        assert totales.total_traslados_base_iva16 == Decimal("25000.00")
        assert totales.total_traslados_impuesto_iva16 == Decimal("4000.00")
        assert totales.total_retenciones_iva == Decimal("0")
        assert totales.total_retenciones_isr == Decimal("0")

    def test_pago_count(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        assert len(data.pagos) == 1

    def test_pago_fields(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        pago = data.pagos[0]
        assert pago.fecha_pago == datetime(2024, 4, 10, 0, 0, 0)
        assert pago.forma_pago == "03"  # Transferencia
        assert pago.monto == Decimal("29000.00")
        assert pago.moneda == "MXN"
        assert isinstance(pago.tipo_cambio, Decimal)

    def test_doctos_relacionados(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        pago = data.pagos[0]
        assert len(pago.doctos_relacionados) == 2

        docto = pago.doctos_relacionados[0]
        assert docto.id_documento == "1A2B3C4D-5E6F-7A8B-9C0D-1E2F3A4B5C6D"
        assert docto.serie == "B"
        assert docto.folio == "67890"
        assert docto.num_parcialidad == 1
        assert docto.imp_saldo_ant == Decimal("29000.00")
        assert docto.imp_pagado == Decimal("14500.00")
        assert docto.imp_saldo_insoluto == Decimal("14500.00")
        assert docto.objeto_imp_dr == "02"

    def test_docto_decimal_types(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        docto = data.pagos[0].doctos_relacionados[0]
        assert isinstance(docto.imp_saldo_ant, Decimal)
        assert isinstance(docto.imp_pagado, Decimal)
        assert isinstance(docto.imp_saldo_insoluto, Decimal)
        assert isinstance(docto.equivalencia, Decimal)

    def test_impuestos_dr(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        docto = data.pagos[0].doctos_relacionados[0]
        assert len(docto.impuestos_dr) == 1
        tax = docto.impuestos_dr[0]
        assert tax.base_dr == Decimal("12500.00")
        assert tax.impuesto_dr == "002"  # IVA
        assert tax.tipo_factor_dr == "Tasa"
        assert tax.tasa_o_cuota_dr == Decimal("0.160000")
        assert tax.importe_dr == Decimal("2000.00")
        assert tax.tipo == "traslado"

    def test_second_docto(self, pago_20_xml: bytes) -> None:
        result = parse_pago(pago_20_xml)
        data = result.data
        assert isinstance(data, ComplementoPago20)
        docto2 = data.pagos[0].doctos_relacionados[1]
        assert docto2.id_documento == "AABB1122-3344-5566-7788-99AABBCCDDEE"
        assert docto2.serie == "A"
        assert docto2.folio == "11111"


class TestPago20Errors:
    """Test error handling for invalid Pago XML."""

    def test_malformed_xml(self) -> None:
        result = parse_pago(b"<<invalid")
        assert not result.es_valido
        assert "XML mal formado" in result.errores[0]

    def test_no_complemento(self) -> None:
        xml = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
            Version="4.0" TipoDeComprobante="P"
            SubTotal="0" Total="0" Moneda="XXX">
        </cfdi:Comprobante>"""
        result = parse_pago(xml)
        assert not result.es_valido
        assert any("Complemento" in e for e in result.errores)

    def test_no_pagos_node(self) -> None:
        xml = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
            Version="4.0" TipoDeComprobante="P"
            SubTotal="0" Total="0" Moneda="XXX">
            <cfdi:Complemento/>
        </cfdi:Comprobante>"""
        result = parse_pago(xml)
        assert not result.es_valido
        assert any("Pagos 2.0" in e for e in result.errores)
