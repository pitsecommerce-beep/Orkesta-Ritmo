"""
Tests para calculo de ISR RESICO Persona Fisica.

Cada test tiene el resultado esperado calculado a mano.
"""

from decimal import Decimal

import pytest

from tax_engine.clasificador import clasificar_cfdis
from tax_engine.resico_pf import calcular_isr_resico_pf
from tax_engine.engine import calcular
from tax_engine.types import (
    CfdiNormalizado,
    ComplementoPago,
    DoctoRelacionado,
    ImpuestoDR,
    ImpuestoRetenido,
    ImpuestoTrasladado,
    PerfilFiscal,
    Regimen,
)
from tests.conftest import make_cfdi_pue, make_cfdi_ppd, make_cfdi_pago


class TestResicoPfISR:
    """Tests de calculo ISR para RESICO PF."""

    def test_01_single_pue_first_bracket(self, ejercicio_2025):
        """
        Un solo CFDI PUE, sin retenciones, ingreso en primer tramo.
        Ingreso: $20,000 -> Tramo 1 (hasta $25,000, tasa 1.00%)
        ISR = 20000 * 1.00% = $200.00
        """
        cfdi = make_cfdi_pue(
            uuid="test-01",
            subtotal=Decimal("20000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("20000")
        assert isr.deducciones == Decimal("0")
        assert isr.base_gravable == Decimal("20000")
        assert isr.impuesto_determinado == Decimal("200")
        assert isr.retenciones_isr == Decimal("0")
        assert isr.isr_a_pagar == Decimal("200")
        assert len(alertas) == 0

    def test_02_single_pue_second_bracket(self, ejercicio_2025):
        """
        Un solo CFDI PUE, ingreso en segundo tramo.
        Ingreso: $40,000 -> Tramo 2 (hasta $50,000, tasa 1.10%)
        ISR = 40000 * 1.10% = $440.00
        """
        cfdi = make_cfdi_pue(
            uuid="test-02",
            subtotal=Decimal("40000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("40000")
        assert isr.impuesto_determinado == Decimal("440")
        assert isr.isr_a_pagar == Decimal("440")
        assert len(alertas) == 0

    def test_03_multiple_pue_third_bracket(self, ejercicio_2025):
        """
        Multiples CFDIs PUE, total en tercer tramo.
        Ingreso: $30,000 + $25,000 = $55,000 -> Tramo 3 (hasta $83,888.33, tasa 1.50%)
        ISR = 55000 * 1.50% = $825.00
        """
        cfdi1 = make_cfdi_pue(uuid="test-03a", subtotal=Decimal("30000"))
        cfdi2 = make_cfdi_pue(uuid="test-03b", subtotal=Decimal("25000"))
        clasificados = clasificar_cfdis([cfdi1, cfdi2])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("55000")
        assert isr.impuesto_determinado == Decimal("825")
        assert isr.isr_a_pagar == Decimal("825")
        assert len(alertas) == 0

    def test_04_pue_with_isr_withholding(self, ejercicio_2025):
        """
        CFDI PUE con retencion ISR de 1.25% (factura a persona moral).
        Ingreso: $20,000 -> Tramo 1 (1.00%)
        ISR determinado = 20000 * 1.00% = $200.00
        Retencion ISR = $250.00 (1.25% de 20000)
        ISR a pagar = 200 - 250 = -$50 (saldo a favor)
        """
        cfdi = make_cfdi_pue(
            uuid="test-04",
            subtotal=Decimal("20000"),
            retenciones_isr=Decimal("250"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("20000")
        assert isr.impuesto_determinado == Decimal("200")
        assert isr.retenciones_isr == Decimal("250")
        assert isr.isr_a_pagar == Decimal("-50")
        # Should have alert about saldo a favor
        assert any("saldo a favor" in a.lower() or "Saldo a favor" in a for a in alertas)

    def test_05_ppd_excluded(self, ejercicio_2025):
        """
        CFDI PPD debe ser excluido (no tiene complemento de pago).
        Solo el PPD: ingreso = 0, ISR = 0.
        """
        cfdi = make_cfdi_ppd(uuid="test-05", subtotal=Decimal("50000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("0")
        assert isr.impuesto_determinado == Decimal("0")
        assert isr.isr_a_pagar == Decimal("0")

    def test_06_cancelled_cfdi_excluded(self, ejercicio_2025):
        """
        CFDI cancelado debe ser excluido.
        """
        cfdi = make_cfdi_pue(
            uuid="test-06",
            subtotal=Decimal("30000"),
            estado="cancelado",
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("0")
        assert isr.impuesto_determinado == Decimal("0")
        assert isr.isr_a_pagar == Decimal("0")

    def test_07_payment_complement_objeto_imp_02(self, ejercicio_2025):
        """
        Complemento de pago (Tipo P) con ObjetoImpDR=02.
        Monto pagado: $11,600 (incluye IVA 16%)
        Base = 11600 / 1.16 = $10,000
        Ingreso: $10,000 -> Tramo 1 (1.00%)
        ISR = 10000 * 1.00% = $100.00
        """
        cfdi = make_cfdi_pago(
            uuid="test-07",
            uuid_docto="docto-07",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        # 11600 / 1.16 = 10000
        assert isr.ingresos == Decimal("10000")
        assert isr.impuesto_determinado == Decimal("100")
        assert isr.isr_a_pagar == Decimal("100")

    def test_08_payment_complement_objeto_imp_01(self, ejercicio_2025):
        """
        Complemento de pago (Tipo P) con ObjetoImpDR=01 (sin IVA).
        Monto pagado: $10,000 = base completa (no se divide)
        Ingreso: $10,000 -> Tramo 1 (1.00%)
        ISR = 10000 * 1.00% = $100.00
        """
        cfdi = make_cfdi_pago(
            uuid="test-08",
            uuid_docto="docto-08",
            monto_pagado=Decimal("10000"),
            objeto_imp_dr="01",
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("10000")
        assert isr.impuesto_determinado == Decimal("100")
        assert isr.isr_a_pagar == Decimal("100")

    def test_09_mixed_pue_and_pago(self, ejercicio_2025):
        """
        Mezcla de PUE y complemento de pago en mismo periodo.
        PUE: $15,000
        Pago: $11,600 -> base $10,000
        Total: $25,000 -> Tramo 1 (1.00%)
        ISR = 25000 * 1.00% = $250.00
        """
        cfdi_pue = make_cfdi_pue(uuid="test-09a", subtotal=Decimal("15000"))
        cfdi_pago = make_cfdi_pago(
            uuid="test-09b",
            uuid_docto="docto-09",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
        )
        clasificados = clasificar_cfdis([cfdi_pue, cfdi_pago])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("25000")
        assert isr.impuesto_determinado == Decimal("250")
        assert isr.isr_a_pagar == Decimal("250")

    def test_10_exact_bracket_boundary(self, ejercicio_2025):
        """
        Ingreso exactamente en el limite del primer tramo.
        Ingreso: $25,000.00 -> Tramo 1 (hasta $25,000.00, tasa 1.00%)
        ISR = 25000 * 1.00% = $250.00
        """
        cfdi = make_cfdi_pue(uuid="test-10", subtotal=Decimal("25000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("25000")
        assert isr.impuesto_determinado == Decimal("250")
        assert isr.isr_a_pagar == Decimal("250")
        assert len(alertas) == 0

    def test_11_income_exceeds_all_brackets(self, ejercicio_2025):
        """
        Ingreso que excede todos los tramos RESICO.
        Ingreso: $300,000 -> Excede tramo 5 ($291,666.66)
        Debe generar alerta.
        """
        cfdi = make_cfdi_pue(uuid="test-11", subtotal=Decimal("300000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("300000")
        # Should apply last bracket rate as estimate: 300000 * 2.50% = 7500
        assert isr.impuesto_determinado == Decimal("7500")
        assert len(alertas) > 0
        assert any("excede" in a.lower() for a in alertas)

    def test_12_fourth_bracket(self, ejercicio_2025):
        """
        Ingreso en cuarto tramo.
        Ingreso: $150,000 -> Tramo 4 (hasta $208,333.33, tasa 2.00%)
        ISR = 150000 * 2.00% = $3,000.00
        """
        cfdi = make_cfdi_pue(uuid="test-12", subtotal=Decimal("150000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("150000")
        assert isr.impuesto_determinado == Decimal("3000")
        assert isr.isr_a_pagar == Decimal("3000")

    def test_13_fifth_bracket(self, ejercicio_2025):
        """
        Ingreso en quinto tramo.
        Ingreso: $250,000 -> Tramo 5 (hasta $291,666.66, tasa 2.50%)
        ISR = 250000 * 2.50% = $6,250.00
        """
        cfdi = make_cfdi_pue(uuid="test-13", subtotal=Decimal("250000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        assert isr.ingresos == Decimal("250000")
        assert isr.impuesto_determinado == Decimal("6250")
        assert isr.isr_a_pagar == Decimal("6250")

    def test_14_traceability(self, ejercicio_2025):
        """
        Verificar que la trazabilidad incluye UUIDs de CFDIs.
        """
        cfdi1 = make_cfdi_pue(uuid="trace-01", subtotal=Decimal("10000"))
        cfdi2 = make_cfdi_pue(uuid="trace-02", subtotal=Decimal("5000"))
        clasificados = clasificar_cfdis([cfdi1, cfdi2])
        isr, _ = calcular_isr_resico_pf(
            clasificados, ejercicio_2025.tarifas_resico
        )

        uuids = [t.uuid for t in isr.trazabilidad]
        assert "trace-01" in uuids
        assert "trace-02" in uuids

    def test_15_engine_integration_resico_pf(self, perfil_resico_pf):
        """
        Test de integracion a traves del engine.calcular().
        Ingreso: $20,000 -> ISR = $200
        """
        cfdi = make_cfdi_pue(uuid="engine-01", subtotal=Decimal("20000"))
        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil_resico_pf,
            ejercicio_year=2025,
            periodo=1,
        )

        assert resultado.isr.ingresos == Decimal("20000")
        assert resultado.isr.impuesto_determinado == Decimal("200")
        assert resultado.periodo_ejercicio == 2025
        assert resultado.periodo_numero == 1
