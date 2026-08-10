"""
Tests para calculo de IVA.
"""

from decimal import Decimal

import pytest

from tax_engine.clasificador import clasificar_cfdis
from tax_engine.iva import calcular_iva
from tax_engine.types import (
    CfdiNormalizado,
    ImpuestoRetenido,
    ImpuestoTrasladado,
    ResultadoActividad,
    ResultadoClasificacion,
)
from tests.conftest import make_cfdi_pue, make_cfdi_pago


class TestIVA:
    """Tests de calculo de IVA."""

    def test_01_simple_iva16(self):
        """
        Actividad con IVA 16%.
        Ingreso base: $10,000
        IVA trasladado: 10000 * 16% = $1,600
        Sin retenciones ni acreditable.
        IVA a pagar = $1,600
        """
        cfdi = make_cfdi_pue(
            uuid="iva-01",
            subtotal=Decimal("10000"),
            iva_tasa=Decimal("0.160000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            clasificaciones_actividad=[
                ResultadoActividad(
                    actividad_id="iva-01",
                    resultado=ResultadoClasificacion.IVA16,
                )
            ],
            cfdis_recibidos=[],
        )

        assert iva.iva_trasladado == Decimal("1600")
        assert iva.iva_retenido == Decimal("0")
        assert iva.iva_acreditable == Decimal("0")
        assert iva.iva_a_pagar == Decimal("1600")
        assert not iva.requiere_revision

    def test_02_iva_tasa_cero(self):
        """
        Actividad con IVA 0%.
        No genera IVA trasladado.
        """
        cfdi = make_cfdi_pue(
            uuid="iva-02",
            subtotal=Decimal("10000"),
            iva_tasa=Decimal("0"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            clasificaciones_actividad=[
                ResultadoActividad(
                    actividad_id="iva-02",
                    resultado=ResultadoClasificacion.IVA0,
                )
            ],
            cfdis_recibidos=[],
        )

        assert iva.iva_trasladado == Decimal("0")
        assert iva.iva_a_pagar == Decimal("0")

    def test_03_exento(self):
        """
        Actividad exenta de IVA.
        No genera IVA trasladado.
        """
        cfdi = make_cfdi_pue(
            uuid="iva-03",
            subtotal=Decimal("10000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            clasificaciones_actividad=[
                ResultadoActividad(
                    actividad_id="iva-03",
                    resultado=ResultadoClasificacion.EXENTO,
                )
            ],
            cfdis_recibidos=[],
        )

        assert iva.iva_trasladado == Decimal("0")
        assert iva.iva_a_pagar == Decimal("0")

    def test_04_iva_with_withholdings(self):
        """
        IVA con retenciones (2/3 de IVA = 10.6667%).
        Ingreso: $10,000
        IVA trasladado: $1,600
        IVA retenido: $1,066.67
        IVA a pagar: 1600 - 1066.67 = $533.33
        """
        cfdi = make_cfdi_pue(
            uuid="iva-04",
            subtotal=Decimal("10000"),
            iva_tasa=Decimal("0.160000"),
            retenciones_iva=Decimal("1066.67"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[],
        )

        assert iva.iva_trasladado == Decimal("1600")
        assert iva.iva_retenido == Decimal("1066.67")
        assert iva.iva_a_pagar == Decimal("1600") - Decimal("1066.67")

    def test_05_acreditable_unknown_requiere_revision(self):
        """
        Sin CFDIs recibidos proporcionados: IVA acreditable desconocido.
        Debe marcar requiere_revision=True y acreditable=0.
        """
        cfdi = make_cfdi_pue(
            uuid="iva-05",
            subtotal=Decimal("10000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=None,
        )

        assert iva.requiere_revision is True
        assert iva.iva_acreditable == Decimal("0")
        assert iva.motivo_revision is not None
        assert len(alertas) > 0

    def test_06_acreditable_from_pue_received(self):
        """
        IVA acreditable de CFDI PUE recibido.
        Gasto: $5,000 con IVA 16% = $800 acreditable.
        """
        cfdi_emitido = make_cfdi_pue(uuid="iva-06e", subtotal=Decimal("10000"))
        cfdi_recibido = CfdiNormalizado(
            uuid="iva-06r",
            tipo="I",
            metodo_pago="PUE",
            fecha_emision="2025-01-10",
            fecha_pago=None,
            rfc_emisor="XAXX010101099",
            rfc_receptor="XAXX010101000",
            subtotal=Decimal("5000"),
            total=Decimal("5800"),
            impuestos_trasladados=[
                ImpuestoTrasladado(
                    impuesto="002",
                    tasa=Decimal("0.160000"),
                    importe=Decimal("800"),
                    base=Decimal("5000"),
                )
            ],
            estado="vigente",
        )

        clasificados = clasificar_cfdis([cfdi_emitido])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[cfdi_recibido],
        )

        assert iva.iva_acreditable == Decimal("800")
        assert iva.iva_a_pagar == Decimal("1600") - Decimal("800")

    def test_07_ppd_recibido_requiere_revision(self):
        """
        CFDI PPD recibido sin complemento: no se puede acreditar.
        """
        cfdi_emitido = make_cfdi_pue(uuid="iva-07e", subtotal=Decimal("10000"))
        cfdi_recibido = CfdiNormalizado(
            uuid="iva-07r",
            tipo="I",
            metodo_pago="PPD",
            fecha_emision="2025-01-10",
            fecha_pago=None,
            rfc_emisor="XAXX010101099",
            rfc_receptor="XAXX010101000",
            subtotal=Decimal("5000"),
            total=Decimal("5800"),
            impuestos_trasladados=[
                ImpuestoTrasladado(
                    impuesto="002",
                    tasa=Decimal("0.160000"),
                    importe=Decimal("800"),
                    base=Decimal("5000"),
                )
            ],
            estado="vigente",
        )

        clasificados = clasificar_cfdis([cfdi_emitido])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[cfdi_recibido],
        )

        assert iva.requiere_revision is True
        assert iva.iva_acreditable == Decimal("0")

    def test_08_nomina_excluded_from_recibidos(self):
        """
        CFDI de nomina recibido: no se mezcla con IVA acreditable.
        """
        cfdi_emitido = make_cfdi_pue(uuid="iva-08e", subtotal=Decimal("10000"))
        cfdi_nomina = CfdiNormalizado(
            uuid="iva-08n",
            tipo="N",
            metodo_pago="PUE",
            fecha_emision="2025-01-15",
            fecha_pago=None,
            rfc_emisor="XAXX010101099",
            rfc_receptor="XAXX010101000",
            subtotal=Decimal("15000"),
            total=Decimal("15000"),
            estado="vigente",
        )

        clasificados = clasificar_cfdis([cfdi_emitido])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[cfdi_nomina],
        )

        # Nomina should not generate IVA acreditable
        assert iva.iva_acreditable == Decimal("0")

    def test_09_cancelled_recibido_excluded(self):
        """
        CFDI recibido cancelado: no genera IVA acreditable.
        """
        cfdi_emitido = make_cfdi_pue(uuid="iva-09e", subtotal=Decimal("10000"))
        cfdi_recibido = CfdiNormalizado(
            uuid="iva-09r",
            tipo="I",
            metodo_pago="PUE",
            fecha_emision="2025-01-10",
            fecha_pago=None,
            rfc_emisor="XAXX010101099",
            rfc_receptor="XAXX010101000",
            subtotal=Decimal("5000"),
            total=Decimal("5800"),
            impuestos_trasladados=[
                ImpuestoTrasladado(
                    impuesto="002",
                    tasa=Decimal("0.160000"),
                    importe=Decimal("800"),
                    base=Decimal("5000"),
                )
            ],
            estado="cancelado",
        )

        clasificados = clasificar_cfdis([cfdi_emitido])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[cfdi_recibido],
        )

        assert iva.iva_acreditable == Decimal("0")

    def test_10_pago_complement_iva(self):
        """
        IVA de complemento de pago con ObjetoImpDR=02.
        Monto pagado: $11,600
        Base: 11600 / 1.16 = $10,000
        IVA trasladado: 11600 - 10000 = $1,600
        """
        cfdi = make_cfdi_pago(
            uuid="iva-10",
            monto_pagado=Decimal("11600"),
            objeto_imp_dr="02",
            tasa_iva_dr=Decimal("0.160000"),
        )
        clasificados = clasificar_cfdis([cfdi])
        iva, alertas = calcular_iva(
            clasificados,
            cfdis_recibidos=[],
        )

        assert iva.iva_trasladado == Decimal("11600") - Decimal("11600") / Decimal("1.16")
