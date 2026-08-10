"""
Tests para calculo de ISR de Arrendamiento.

Cada test tiene el resultado esperado calculado a mano.
Arrendamiento usa deduccion ciega (35%) y tarifa Art. 96.
"""

from decimal import Decimal

import pytest

from tax_engine.clasificador import clasificar_cfdis
from tax_engine.arrendamiento import calcular_isr_arrendamiento
from tax_engine.engine import calcular
from tax_engine.types import PerfilFiscal, Regimen
from tests.conftest import make_cfdi_pue, make_cfdi_ppd, make_cfdi_pago


class TestArrendamientoISR:
    """Tests de calculo ISR para Arrendamiento."""

    def test_01_single_month_first_bracket(self, ejercicio_2025):
        """
        Un mes, ingreso en primer tramo, deduccion ciega.
        Ingreso: $1,000
        Deduccion ciega: 1000 * 35% = $350
        Base gravable: 1000 - 350 = $650
        Tramo 1: lim_inf=0.01, lim_sup=844.59, cuota=0, %=1.92
        ISR = (650 - 0.01) * 1.92% + 0 = 649.99 * 0.0192 = $12.479808
        """
        cfdi = make_cfdi_pue(uuid="arr-01", subtotal=Decimal("1000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("1000")
        assert isr.deducciones == Decimal("350")
        assert isr.base_gravable == Decimal("650")
        # (650 - 0.01) * 1.92 / 100 + 0 = 649.99 * 0.0192 = 12.479808
        expected_isr = (Decimal("650") - Decimal("0.01")) * Decimal("1.92") / Decimal("100") + Decimal("0")
        assert isr.impuesto_determinado == expected_isr
        assert isr.isr_a_pagar == expected_isr

    def test_02_middle_bracket(self, ejercicio_2025):
        """
        Ingreso en tramo medio.
        Ingreso: $30,000
        Deduccion ciega: 30000 * 35% = $10,500
        Base gravable: 30000 - 10500 = $19,500
        Tramo 6: lim_inf=17533.65, lim_sup=35362.83, cuota=1856.84, %=21.36
        ISR = (19500 - 17533.65) * 21.36% + 1856.84
            = 1966.35 * 0.2136 + 1856.84
            = 420.013560 + 1856.84
            = $2276.853560
        """
        cfdi = make_cfdi_pue(uuid="arr-02", subtotal=Decimal("30000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("30000")
        assert isr.deducciones == Decimal("10500")
        assert isr.base_gravable == Decimal("19500")
        excedente = Decimal("19500") - Decimal("17533.65")
        expected = excedente * Decimal("21.36") / Decimal("100") + Decimal("1856.84")
        assert isr.impuesto_determinado == expected

    def test_03_top_bracket(self, ejercicio_2025):
        """
        Ingreso en tramo superior (sin limite superior).
        Ingreso: $700,000
        Deduccion ciega: 700000 * 35% = $245,000
        Base gravable: 700000 - 245000 = $455,000
        Tramo 11: lim_inf=425642.00, cuota=133488.54, %=35.00
        ISR = (455000 - 425642) * 35% + 133488.54
            = 29358 * 0.35 + 133488.54
            = 10275.30 + 133488.54
            = $143,763.84
        """
        cfdi = make_cfdi_pue(uuid="arr-03", subtotal=Decimal("700000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("700000")
        assert isr.deducciones == Decimal("245000")
        assert isr.base_gravable == Decimal("455000")
        excedente = Decimal("455000") - Decimal("425642")
        expected = excedente * Decimal("35") / Decimal("100") + Decimal("133488.54")
        assert isr.impuesto_determinado == expected

    def test_04_with_isr_withholding(self, ejercicio_2025):
        """
        Con retencion ISR del 10% (factura a persona moral).
        Ingreso: $20,000
        Deduccion ciega: 20000 * 35% = $7,000
        Base gravable: 20000 - 7000 = $13,000
        Tramo 4: lim_inf=12598.03, lim_sup=14644.64, cuota=1011.68, %=16.00
        ISR = (13000 - 12598.03) * 16% + 1011.68
            = 401.97 * 0.16 + 1011.68
            = 64.3152 + 1011.68
            = $1075.9952
        Retencion ISR: $2,000 (10% de 20000)
        ISR a pagar = 1075.9952 - 2000 = -$924.0048 (saldo a favor)
        """
        cfdi = make_cfdi_pue(
            uuid="arr-04",
            subtotal=Decimal("20000"),
            retenciones_isr=Decimal("2000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("20000")
        assert isr.deducciones == Decimal("7000")
        assert isr.base_gravable == Decimal("13000")
        excedente = Decimal("13000") - Decimal("12598.03")
        imp_det = excedente * Decimal("16") / Decimal("100") + Decimal("1011.68")
        assert isr.impuesto_determinado == imp_det
        assert isr.retenciones_isr == Decimal("2000")
        assert isr.isr_a_pagar == imp_det - Decimal("2000")
        assert isr.isr_a_pagar < Decimal("0")

    def test_05_with_iva_withholding(self, ejercicio_2025):
        """
        Con retencion IVA de 2/3 (no afecta ISR, solo verificar que se lee).
        Ingreso: $20,000
        Deduccion ciega: $7,000
        Base gravable: $13,000
        ISR calculado normalmente, retencion IVA no afecta ISR.
        """
        cfdi = make_cfdi_pue(
            uuid="arr-05",
            subtotal=Decimal("20000"),
            retenciones_iva=Decimal("2133.33"),  # 2/3 of 3200 (IVA 16% on 20000)
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        # IVA withholding should not affect ISR calculation
        assert isr.ingresos == Decimal("20000")
        assert isr.deducciones == Decimal("7000")
        assert isr.retenciones_isr == Decimal("0")
        excedente = Decimal("13000") - Decimal("12598.03")
        imp_det = excedente * Decimal("16") / Decimal("100") + Decimal("1011.68")
        assert isr.impuesto_determinado == imp_det

    def test_06_trimestral_option(self, ejercicio_2025):
        """
        Opcion trimestral: tarifa triplicada.
        Ingreso trimestral: $60,000
        Deduccion ciega: 60000 * 35% = $21,000
        Base gravable: 60000 - 21000 = $39,000

        Tarifa triplicada tramo 6:
        lim_inf = 17533.65 * 3 = 52600.95
        cuota_fija = 1856.84 * 3 = 5570.52
        % = 21.36

        Pero 39000 < 52600.95, so use tramo 5 triplicado:
        lim_inf = 14644.65 * 3 = 43933.95
        cuota_fija = 1339.14 * 3 = 4017.42
        % = 17.92

        But 39000 < 43933.95, so use tramo 4 triplicado:
        lim_inf = 12598.03 * 3 = 37794.09
        lim_sup = 14644.64 * 3 = 43933.92
        cuota_fija = 1011.68 * 3 = 3035.04
        % = 16.00

        ISR = (39000 - 37794.09) * 16% + 3035.04
            = 1205.91 * 0.16 + 3035.04
            = 192.9456 + 3035.04
            = $3227.9856
        """
        cfdi1 = make_cfdi_pue(uuid="arr-06a", subtotal=Decimal("20000"))
        cfdi2 = make_cfdi_pue(uuid="arr-06b", subtotal=Decimal("20000"))
        cfdi3 = make_cfdi_pue(uuid="arr-06c", subtotal=Decimal("20000"))
        clasificados = clasificar_cfdis([cfdi1, cfdi2, cfdi3])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados,
            ejercicio_2025.tarifas_art96,
            opcion_trimestral=True,
        )

        assert isr.ingresos == Decimal("60000")
        assert isr.deducciones == Decimal("21000")
        assert isr.base_gravable == Decimal("39000")
        excedente = Decimal("39000") - Decimal("37794.09")
        expected = excedente * Decimal("16") / Decimal("100") + Decimal("3035.04")
        assert isr.impuesto_determinado == expected

    def test_07_ppd_excluded(self, ejercicio_2025):
        """
        CFDI PPD debe ser excluido en arrendamiento.
        """
        cfdi = make_cfdi_ppd(uuid="arr-07", subtotal=Decimal("30000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("0")
        assert isr.impuesto_determinado == Decimal("0")

    def test_08_cancelled_excluded(self, ejercicio_2025):
        """
        CFDI cancelado debe ser excluido en arrendamiento.
        """
        cfdi = make_cfdi_pue(
            uuid="arr-08",
            subtotal=Decimal("20000"),
            estado="cancelado",
        )
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("0")
        assert isr.impuesto_determinado == Decimal("0")

    def test_09_blind_deduction_verification(self, ejercicio_2025):
        """
        Verificar calculo exacto de deduccion ciega al 35%.
        Ingreso: $45,678.90
        Deduccion: 45678.90 * 0.35 = $15,987.615
        Base: 45678.90 - 15987.615 = $29,691.285
        """
        cfdi = make_cfdi_pue(uuid="arr-09", subtotal=Decimal("45678.90"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        expected_deduccion = Decimal("45678.90") * Decimal("35") / Decimal("100")
        assert isr.deducciones == expected_deduccion
        assert isr.base_gravable == Decimal("45678.90") - expected_deduccion

    def test_10_multiple_cfdis_single_period(self, ejercicio_2025):
        """
        Multiples CFDIs en un solo periodo mensual.
        Ingresos: $8,000 + $12,000 + $5,000 = $25,000
        Deduccion ciega: 25000 * 35% = $8,750
        Base gravable: 25000 - 8750 = $16,250
        Tramo 5: lim_inf=14644.65, lim_sup=17533.64, cuota=1339.14, %=17.92
        ISR = (16250 - 14644.65) * 17.92% + 1339.14
            = 1605.35 * 0.1792 + 1339.14
            = 287.598720 + 1339.14
            = $1626.738720
        """
        cfdi1 = make_cfdi_pue(uuid="arr-10a", subtotal=Decimal("8000"))
        cfdi2 = make_cfdi_pue(uuid="arr-10b", subtotal=Decimal("12000"))
        cfdi3 = make_cfdi_pue(uuid="arr-10c", subtotal=Decimal("5000"))
        clasificados = clasificar_cfdis([cfdi1, cfdi2, cfdi3])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("25000")
        assert isr.deducciones == Decimal("8750")
        assert isr.base_gravable == Decimal("16250")
        excedente = Decimal("16250") - Decimal("14644.65")
        expected = excedente * Decimal("17.92") / Decimal("100") + Decimal("1339.14")
        assert isr.impuesto_determinado == expected

    def test_11_second_bracket(self, ejercicio_2025):
        """
        Ingreso que resulta en base gravable en segundo tramo.
        Ingreso: $5,000
        Deduccion ciega: 5000 * 35% = $1,750
        Base gravable: 5000 - 1750 = $3,250
        Tramo 2: lim_inf=844.60, lim_sup=7168.51, cuota=16.22, %=6.40
        ISR = (3250 - 844.60) * 6.40% + 16.22
            = 2405.40 * 0.0640 + 16.22
            = 153.9456 + 16.22
            = $170.1656
        """
        cfdi = make_cfdi_pue(uuid="arr-11", subtotal=Decimal("5000"))
        clasificados = clasificar_cfdis([cfdi])
        isr, alertas = calcular_isr_arrendamiento(
            clasificados, ejercicio_2025.tarifas_art96
        )

        assert isr.ingresos == Decimal("5000")
        assert isr.deducciones == Decimal("1750")
        assert isr.base_gravable == Decimal("3250")
        excedente = Decimal("3250") - Decimal("844.60")
        expected = excedente * Decimal("6.40") / Decimal("100") + Decimal("16.22")
        assert isr.impuesto_determinado == expected

    def test_12_engine_integration_arrendamiento(self, perfil_arrendamiento):
        """
        Test de integracion a traves del engine.calcular().
        """
        cfdi = make_cfdi_pue(uuid="arr-eng-01", subtotal=Decimal("20000"))
        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil_arrendamiento,
            ejercicio_year=2025,
            periodo=3,
        )

        assert resultado.isr.ingresos == Decimal("20000")
        assert resultado.isr.deducciones == Decimal("7000")
        assert resultado.periodo_ejercicio == 2025
        assert resultado.periodo_numero == 3

    def test_13_engine_integration_trimestral(self, perfil_arrendamiento_trimestral):
        """
        Test de integracion trimestral a traves del engine.
        """
        cfdi = make_cfdi_pue(uuid="arr-eng-02", subtotal=Decimal("60000"))
        resultado = calcular(
            cfdis_emitidos=[cfdi],
            perfil=perfil_arrendamiento_trimestral,
            ejercicio_year=2025,
            periodo=1,
        )

        assert resultado.isr.ingresos == Decimal("60000")
        assert resultado.isr.deducciones == Decimal("21000")
