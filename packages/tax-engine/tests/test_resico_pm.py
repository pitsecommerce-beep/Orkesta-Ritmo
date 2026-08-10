"""
Tests para calculo de ISR RESICO Persona Moral.
"""

from decimal import Decimal

import pytest

from tax_engine.clasificador import clasificar_cfdis
from tax_engine.resico_pm import calcular_isr_resico_pm
from tax_engine.engine import calcular
from tax_engine.types import PerfilFiscal, Regimen
from tests.conftest import make_cfdi_pue, make_cfdi_ppd, make_cfdi_pago


class TestResicoPmISR:
    """Tests de calculo ISR para RESICO PM."""

    def test_01_single_pue_first_bracket(self, ejercicio_2025):
        """
        Un solo CFDI PUE, ingreso en primer tramo.
        Ingreso: $20,000 -> Tramo 1 (1.00%)
        ISR = 20000 * 1.00% = $200.00
        """
        cfdi = make_cfdi_pue(
            uuid="pm-01",
            subtotal=Decimal("20000"),
            rfc_emisor="XAX010101000",  # 12 digitos PM
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("20000")
        assert isr.impuesto_determinado == Decimal("200")
        assert isr.isr_a_pagar == Decimal("200")

    def test_02_second_bracket(self, ejercicio_2025):
        """
        Ingreso en segundo tramo.
        Ingreso: $35,000 -> Tramo 2 (1.10%)
        ISR = 35000 * 1.10% = $385.00
        """
        cfdi = make_cfdi_pue(uuid="pm-02", subtotal=Decimal("35000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("35000")
        assert isr.impuesto_determinado == Decimal("385")

    def test_03_with_withholdings(self, ejercicio_2025):
        """
        Con retenciones ISR.
        Ingreso: $20,000 -> ISR = $200
        Retencion: $50
        ISR a pagar: $150
        """
        cfdi = make_cfdi_pue(
            uuid="pm-03",
            subtotal=Decimal("20000"),
            retenciones_isr=Decimal("50"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.isr_a_pagar == Decimal("150")

    def test_04_no_deductions(self, ejercicio_2025):
        """
        RESICO PM no tiene deducciones en pago provisional.
        """
        cfdi = make_cfdi_pue(uuid="pm-04", subtotal=Decimal("15000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.deducciones == Decimal("0")
        assert isr.base_gravable == isr.ingresos

    def test_05_cancelled_excluded(self, ejercicio_2025):
        """
        CFDI cancelado excluido.
        """
        cfdi = make_cfdi_pue(
            uuid="pm-05",
            subtotal=Decimal("20000"),
            estado="cancelado",
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("0")

    def test_06_engine_integration(self, perfil_resico_pm):
        """
        Integracion a traves del engine.
        """
        cfdi = make_cfdi_pue(uuid="pm-06", subtotal=Decimal("20000"))
        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil_resico_pm,
            ejercicio_year=2025,
            periodo=1,
        )

        assert resultado.isr.ingresos == Decimal("20000")
        assert resultado.isr.impuesto_determinado == Decimal("200")

    def test_07_exceeds_all_brackets(self, ejercicio_2025):
        """
        Ingreso que excede todos los tramos: genera alerta.
        """
        cfdi = make_cfdi_pue(uuid="pm-07", subtotal=Decimal("300000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert len(alertas) > 0
        assert any("excede" in a.lower() for a in alertas)

    def test_08_payment_complement(self, ejercicio_2025):
        """
        Complemento de pago tipo P.
        Monto: $11,600, ObjetoImpDR=02, tasa 16%
        Base = 11600 / 1.16 = $10,000
        ISR = 10000 * 1.00% = $100
        """
        cfdi = make_cfdi_pago(
            uuid="pm-08",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pm(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("10000")
        assert isr.impuesto_determinado == Decimal("100")
