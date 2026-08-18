"""Tests para el adaptador entre catalogo normativo y motor de calculo.

Verifica que el adaptador construye Ejercicio correctamente desde el catalogo,
que la trazabilidad contiene los IDs reales, y que el motor produce resultados
correctos para enero vs marzo 2026 (UMA distinta).
"""

import datetime
from decimal import Decimal

import pytest

from tax_engine.catalogo_adapter import (
    EjercicioResuelto,
    MetadataResolucion,
    fecha_causacion_de_periodo,
    resolver_ejercicio,
)
from tax_engine.catalogo_data import obtener_catalogo
from tax_engine.engine import calcular
from tax_engine.types import PerfilFiscal, Regimen

from tests.conftest import make_cfdi_pue


class TestFechaCausacion:
    """Derivacion de fecha de causacion desde ejercicio + periodo."""

    def test_enero_mensual(self):
        assert fecha_causacion_de_periodo(2026, 1) == datetime.date(2026, 1, 31)

    def test_febrero_mensual_bisiesto(self):
        assert fecha_causacion_de_periodo(2028, 2) == datetime.date(2028, 2, 29)

    def test_febrero_mensual_no_bisiesto(self):
        assert fecha_causacion_de_periodo(2026, 2) == datetime.date(2026, 2, 28)

    def test_marzo_mensual(self):
        assert fecha_causacion_de_periodo(2026, 3) == datetime.date(2026, 3, 31)

    def test_diciembre_mensual(self):
        assert fecha_causacion_de_periodo(2026, 12) == datetime.date(2026, 12, 31)

    def test_trimestre_1(self):
        assert fecha_causacion_de_periodo(2026, 1, trimestral=True) == datetime.date(2026, 3, 31)

    def test_trimestre_2(self):
        assert fecha_causacion_de_periodo(2026, 2, trimestral=True) == datetime.date(2026, 6, 30)

    def test_trimestre_4(self):
        assert fecha_causacion_de_periodo(2026, 4, trimestral=True) == datetime.date(2026, 12, 31)

    def test_periodo_invalido(self):
        with pytest.raises(ValueError):
            fecha_causacion_de_periodo(2026, 13)


class TestResolverEjercicio:
    """Construccion de Ejercicio desde catalogo."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_enero_2026_usa_uma_2025(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        uma_esperada = Decimal("113.14") * Decimal("30.4")
        assert res.ejercicio.umas_mensuales == uma_esperada

    def test_marzo_2026_usa_uma_2026(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 3, 31))
        uma_esperada = Decimal("117.31") * Decimal("30.4")
        assert res.ejercicio.umas_mensuales == uma_esperada

    def test_umas_distintas_enero_vs_marzo_2026(self):
        res_ene = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        res_mar = resolver_ejercicio(self.cat, datetime.date(2026, 3, 31))
        assert res_mar.ejercicio.umas_mensuales > res_ene.ejercicio.umas_mensuales

    def test_tiene_tarifas_resico(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert len(res.ejercicio.tarifas_resico) == 5

    def test_tiene_tarifas_art96(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert len(res.ejercicio.tarifas_art96) == 11

    def test_year_es_correcto(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 3, 31))
        assert res.ejercicio.year == 2026

    def test_ejercicio_2025_funciona(self):
        res = resolver_ejercicio(self.cat, datetime.date(2025, 6, 30))
        assert res.ejercicio.year == 2025
        assert len(res.ejercicio.tarifas_resico) == 5


class TestMetadataResolucion:
    """La metadata contiene IDs reales del catalogo."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_tiene_tarifa_resico_id(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert res.metadata.tarifa_resico_id == "RESICO_PF_MENSUAL_2026"

    def test_tiene_tarifa_art96_id(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert res.metadata.tarifa_art96_id == "ART96_MENSUAL_2026"

    def test_tiene_indicador_uma_id_enero(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert res.metadata.indicador_uma_id == "UMA_DIARIA_2025"

    def test_tiene_indicador_uma_id_marzo(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 3, 31))
        assert res.metadata.indicador_uma_id == "UMA_DIARIA_2026"

    def test_tarifas_usadas_no_vacio(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert len(res.metadata.tarifas_usadas) >= 2

    def test_indicadores_usados_no_vacio(self):
        res = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        assert len(res.metadata.indicadores_usados) >= 1

    def test_ids_distintos_enero_vs_marzo(self):
        res_ene = resolver_ejercicio(self.cat, datetime.date(2026, 1, 31))
        res_mar = resolver_ejercicio(self.cat, datetime.date(2026, 3, 31))
        assert res_ene.metadata.indicador_uma_id != res_mar.metadata.indicador_uma_id


class TestCalculoEndToEndConCatalogo:
    """Calculo completo usando Ejercicio del catalogo en vez del fallback."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_resico_pf_enero_2026(self):
        fecha = fecha_causacion_de_periodo(2026, 1)
        res = resolver_ejercicio(self.cat, fecha)
        cfdi = make_cfdi_pue(subtotal=Decimal("30000"), fecha_emision="2026-01-15")
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil,
            ejercicio_year=2026,
            periodo=1,
            ejercicio=res.ejercicio,
        )
        assert resultado.isr.ingresos == Decimal("30000")
        assert resultado.isr.impuesto_determinado == Decimal("30000") * Decimal("1.10") / Decimal("100")

    def test_resico_pf_marzo_2026(self):
        fecha = fecha_causacion_de_periodo(2026, 3)
        res = resolver_ejercicio(self.cat, fecha)
        cfdi = make_cfdi_pue(subtotal=Decimal("30000"), fecha_emision="2026-03-15")
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil,
            ejercicio_year=2026,
            periodo=3,
            ejercicio=res.ejercicio,
        )
        assert resultado.isr.ingresos == Decimal("30000")
        assert resultado.isr.impuesto_determinado == Decimal("30000") * Decimal("1.10") / Decimal("100")

    def test_arrendamiento_enero_2026_uma_correcta(self):
        fecha = fecha_causacion_de_periodo(2026, 1)
        res = resolver_ejercicio(self.cat, fecha)
        uma_esperada_2025 = Decimal("113.14") * Decimal("30.4")
        assert res.ejercicio.umas_mensuales == uma_esperada_2025

        cfdi = make_cfdi_pue(subtotal=Decimal("20000"), fecha_emision="2026-01-15")
        perfil = PerfilFiscal(regimen=Regimen.ARRENDAMIENTO, rfc="XAXX010101000")

        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil,
            ejercicio_year=2026,
            periodo=1,
            ejercicio=res.ejercicio,
        )
        assert resultado.isr.ingresos == Decimal("20000")
        assert resultado.isr.deducciones == Decimal("20000") * Decimal("35") / Decimal("100")

    def test_arrendamiento_marzo_2026_uma_correcta(self):
        fecha = fecha_causacion_de_periodo(2026, 3)
        res = resolver_ejercicio(self.cat, fecha)
        uma_esperada_2026 = Decimal("117.31") * Decimal("30.4")
        assert res.ejercicio.umas_mensuales == uma_esperada_2026

    def test_no_usa_fallback(self):
        """Cuando se pasa ejercicio explicitamente, el fallback no se invoca."""
        fecha = fecha_causacion_de_periodo(2026, 1)
        res = resolver_ejercicio(self.cat, fecha)

        cfdi = make_cfdi_pue(subtotal=Decimal("10000"), fecha_emision="2026-01-15")
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil,
            ejercicio_year=2026,
            periodo=1,
            ejercicio=res.ejercicio,
        )
        assert resultado.isr.impuesto_determinado == Decimal("10000") * Decimal("1.00") / Decimal("100")


class TestResolucionCalculoPayload:
    """El payload para resolucion_calculo contiene referencias reales."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_payload_enero_2026(self):
        fecha = fecha_causacion_de_periodo(2026, 1)
        res = resolver_ejercicio(self.cat, fecha)

        cfdi = make_cfdi_pue(subtotal=Decimal("30000"), fecha_emision="2026-01-15")
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil,
            ejercicio_year=2026,
            periodo=1,
            ejercicio=res.ejercicio,
        )

        payload = {
            "fecha_causacion": str(res.metadata.fecha_causacion),
            "tarifas_usadas": res.metadata.tarifas_usadas,
            "indicadores_usados": res.metadata.indicadores_usados,
            "resultado_json": {
                "isr_a_cargo": str(resultado.isr.isr_a_cargo),
                "estado": resultado.estado,
            },
        }
        assert payload["tarifas_usadas"][0]["tarifa_id"] == "RESICO_PF_MENSUAL_2026"
        assert payload["indicadores_usados"][0]["indicador_id"] == "UMA_DIARIA_2025"

    def test_payload_marzo_2026_indicador_distinto(self):
        fecha_ene = fecha_causacion_de_periodo(2026, 1)
        fecha_mar = fecha_causacion_de_periodo(2026, 3)
        res_ene = resolver_ejercicio(self.cat, fecha_ene)
        res_mar = resolver_ejercicio(self.cat, fecha_mar)

        assert res_ene.metadata.indicadores_usados[0]["indicador_id"] == "UMA_DIARIA_2025"
        assert res_mar.metadata.indicadores_usados[0]["indicador_id"] == "UMA_DIARIA_2026"
        assert res_ene.metadata.indicadores_usados[0]["indicador_id"] != res_mar.metadata.indicadores_usados[0]["indicador_id"]
