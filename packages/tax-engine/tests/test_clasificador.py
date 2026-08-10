"""
Tests para el clasificador de CFDIs.
"""

from decimal import Decimal

import pytest

from tax_engine.clasificador import clasificar_cfdi, clasificar_cfdis
from tax_engine.types import (
    CfdiNormalizado,
    ComplementoPago,
    DoctoRelacionado,
    ImpuestoDR,
    ImpuestoRetenido,
    ImpuestoTrasladado,
)
from tests.conftest import make_cfdi_pue, make_cfdi_ppd, make_cfdi_pago


class TestClasificador:
    """Tests del clasificador de CFDIs."""

    def test_01_pue_included(self):
        """
        CFDI tipo I con PUE debe ser considerado.
        Base se toma del campo Base de impuestos trasladados.
        """
        cfdi = make_cfdi_pue(uuid="clas-01", subtotal=Decimal("10000"))
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        r = resultados[0]
        assert r.considerado is True
        assert r.motivo == "Ingreso PUE"
        assert r.ingreso_base == Decimal("10000")

    def test_02_ppd_excluded(self):
        """
        CFDI tipo I con PPD no debe ser considerado.
        """
        cfdi = make_cfdi_ppd(uuid="clas-02", subtotal=Decimal("50000"))
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        r = resultados[0]
        assert r.considerado is False
        assert "PPD" in r.motivo

    def test_03_tipo_p_included(self):
        """
        CFDI tipo P (pago) debe ser considerado.
        """
        cfdi = make_cfdi_pago(
            uuid="clas-03",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) >= 1
        r = resultados[0]
        assert r.considerado is True
        assert r.es_pago is True

    def test_04_cancelled_excluded(self):
        """
        CFDI cancelado debe ser excluido independientemente del tipo.
        """
        cfdi = make_cfdi_pue(
            uuid="clas-04",
            subtotal=Decimal("10000"),
            estado="cancelado",
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        r = resultados[0]
        assert r.considerado is False
        assert "cancelado" in r.motivo.lower()

    def test_05_tipo_p_objeto_imp_02_adjustment(self):
        """
        Tipo P con ObjetoImpDR=02: monto se divide entre (1 + tasa).
        Monto pagado: $11,600
        Tasa IVA: 16%
        Base = 11600 / 1.16 = $10,000
        IVA = $1,600
        """
        cfdi = make_cfdi_pago(
            uuid="clas-05",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        r = resultados[0]
        assert r.ingreso_base == Decimal("11600") / Decimal("1.160000")
        assert r.iva_trasladado == Decimal("11600") - r.ingreso_base

    def test_06_tipo_p_objeto_imp_01_no_iva(self):
        """
        Tipo P con ObjetoImpDR=01: control, no genera IVA.
        Monto pagado: $10,000 = base completa.
        """
        cfdi = make_cfdi_pago(
            uuid="clas-06",
            monto_pagado=Decimal("10000"),
            objeto_imp_dr="01",
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        r = resultados[0]
        assert r.ingreso_base == Decimal("10000")
        assert r.iva_trasladado == Decimal("0")

    def test_07_tipo_e_not_considered(self):
        """
        CFDI tipo E (Egreso) no se considera en iteracion 1.
        """
        cfdi = CfdiNormalizado(
            uuid="clas-07",
            tipo="E",
            metodo_pago="PUE",
            fecha_emision="2025-01-15",
            fecha_pago=None,
            rfc_emisor="XAXX010101000",
            rfc_receptor="XAXX010101001",
            subtotal=Decimal("5000"),
            total=Decimal("5000"),
            estado="vigente",
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        assert resultados[0].considerado is False

    def test_08_tipo_n_not_considered(self):
        """
        CFDI tipo N (Nomina) no se considera para actividades.
        """
        cfdi = CfdiNormalizado(
            uuid="clas-08",
            tipo="N",
            metodo_pago="PUE",
            fecha_emision="2025-01-15",
            fecha_pago=None,
            rfc_emisor="XAXX010101000",
            rfc_receptor="XAXX010101001",
            subtotal=Decimal("15000"),
            total=Decimal("15000"),
            estado="vigente",
        )
        resultados = clasificar_cfdi(cfdi)

        assert len(resultados) == 1
        assert resultados[0].considerado is False
        assert "nomina" in resultados[0].motivo.lower()

    def test_09_pue_extracts_retenciones(self):
        """
        PUE con retenciones ISR e IVA: se extraen correctamente.
        """
        cfdi = make_cfdi_pue(
            uuid="clas-09",
            subtotal=Decimal("20000"),
            retenciones_isr=Decimal("250"),
            retenciones_iva=Decimal("2133.33"),
        )
        resultados = clasificar_cfdi(cfdi)

        r = resultados[0]
        assert r.isr_retenido == Decimal("250")
        assert r.iva_retenido == Decimal("2133.33")

    def test_10_multiple_cfdis(self):
        """
        Clasificar multiples CFDIs a la vez.
        """
        cfdis = [
            make_cfdi_pue(uuid="clas-10a", subtotal=Decimal("10000")),
            make_cfdi_ppd(uuid="clas-10b", subtotal=Decimal("50000")),
            make_cfdi_pago(
                uuid="clas-10c",
                monto_pagado=Decimal("11600"),
                objeto_imp_dr="02",
            ),
        ]

        resultados = clasificar_cfdis(cfdis)

        # PUE considered, PPD not, Pago considered
        considerados = [r for r in resultados if r.considerado]
        no_considerados = [r for r in resultados if not r.considerado]
        assert len(considerados) == 2
        assert len(no_considerados) == 1

    def test_11_pago_with_retenciones_dr(self):
        """
        Complemento de pago con retenciones en documento relacionado.
        """
        cfdi = make_cfdi_pago(
            uuid="clas-11",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
            isr_retenido_dr=Decimal("125"),
            iva_retenido_dr=Decimal("1066.67"),
        )
        resultados = clasificar_cfdi(cfdi)

        r = resultados[0]
        assert r.isr_retenido == Decimal("125")
        assert r.iva_retenido == Decimal("1066.67")

    def test_12_traceability(self):
        """
        Verificar que la trazabilidad contiene el UUID.
        """
        cfdi = make_cfdi_pue(uuid="clas-12-trace", subtotal=Decimal("10000"))
        resultados = clasificar_cfdi(cfdi)

        r = resultados[0]
        assert len(r.trazabilidad) > 0
        assert r.trazabilidad[0].uuid == "clas-12-trace"
