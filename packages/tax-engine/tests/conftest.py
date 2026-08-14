"""
Fixtures compartidos para tests del motor de calculo fiscal.
"""

import pytest
from decimal import Decimal

from tax_engine.types import (
    CfdiNormalizado,
    ComplementoPago,
    DoctoRelacionado,
    Ejercicio,
    ImpuestoDR,
    ImpuestoRetenido,
    ImpuestoTrasladado,
    PerfilFiscal,
    Regimen,
    TramoArt96,
    TramoResico,
)
from tax_engine.tarifas_fallback import obtener_ejercicio


@pytest.fixture
def ejercicio_2025() -> Ejercicio:
    """Ejercicio fiscal 2025 con todas las tarifas."""
    ej = obtener_ejercicio(2025)
    assert ej is not None
    return ej


@pytest.fixture
def perfil_resico_pf() -> PerfilFiscal:
    """Perfil fiscal RESICO PF."""
    return PerfilFiscal(
        regimen=Regimen.RESICO_PF,
        rfc="XAXX010101000",
    )


@pytest.fixture
def perfil_arrendamiento() -> PerfilFiscal:
    """Perfil fiscal Arrendamiento con deducción opcional."""
    return PerfilFiscal(
        regimen=Regimen.ARRENDAMIENTO,
        rfc="XAXX010101000",
        tipo_deduccion="opcional",
    )


@pytest.fixture
def perfil_arrendamiento_trimestral() -> PerfilFiscal:
    """Perfil fiscal Arrendamiento trimestral con deducción opcional."""
    return PerfilFiscal(
        regimen=Regimen.ARRENDAMIENTO,
        rfc="XAXX010101000",
        tipo_deduccion="opcional",
        opcion_trimestral=True,
    )


@pytest.fixture
def perfil_resico_pm() -> PerfilFiscal:
    """Perfil fiscal RESICO PM."""
    return PerfilFiscal(
        regimen=Regimen.RESICO_PM,
        rfc="XAX010101000",  # 12 digitos
    )


def make_cfdi_pue(
    uuid: str = "uuid-001",
    subtotal: Decimal = Decimal("10000"),
    iva_tasa: Decimal = Decimal("0.160000"),
    rfc_emisor: str = "XAXX010101000",
    rfc_receptor: str = "XAXX010101001",
    retenciones_isr: Decimal = Decimal("0"),
    retenciones_iva: Decimal = Decimal("0"),
    fecha_emision: str = "2025-01-15",
    estado: str = "vigente",
    objeto_imp: str = "02",
) -> CfdiNormalizado:
    """Crea un CFDI tipo I PUE con IVA 16%."""
    iva_importe = subtotal * iva_tasa
    total = subtotal + iva_importe - retenciones_isr - retenciones_iva

    impuestos_trasladados = [
        ImpuestoTrasladado(
            impuesto="002",
            tasa=iva_tasa,
            importe=iva_importe,
            base=subtotal,
        )
    ]

    impuestos_retenidos = []
    if retenciones_isr > Decimal("0"):
        impuestos_retenidos.append(
            ImpuestoRetenido(
                impuesto="001",
                tasa=Decimal("0.0125"),  # Default placeholder
                importe=retenciones_isr,
            )
        )
    if retenciones_iva > Decimal("0"):
        impuestos_retenidos.append(
            ImpuestoRetenido(
                impuesto="002",
                tasa=Decimal("0.106667"),  # 2/3 of 16%
                importe=retenciones_iva,
            )
        )

    return CfdiNormalizado(
        uuid=uuid,
        tipo="I",
        metodo_pago="PUE",
        fecha_emision=fecha_emision,
        fecha_pago=None,
        rfc_emisor=rfc_emisor,
        rfc_receptor=rfc_receptor,
        subtotal=subtotal,
        total=total,
        impuestos_trasladados=impuestos_trasladados,
        impuestos_retenidos=impuestos_retenidos,
        estado=estado,
        objeto_imp=objeto_imp,
    )


def make_cfdi_ppd(
    uuid: str = "uuid-ppd-001",
    subtotal: Decimal = Decimal("50000"),
    fecha_emision: str = "2025-01-10",
) -> CfdiNormalizado:
    """Crea un CFDI tipo I PPD (no debe considerarse sin complemento)."""
    return CfdiNormalizado(
        uuid=uuid,
        tipo="I",
        metodo_pago="PPD",
        fecha_emision=fecha_emision,
        fecha_pago=None,
        rfc_emisor="XAXX010101000",
        rfc_receptor="XAXX010101001",
        subtotal=subtotal,
        total=subtotal * Decimal("1.16"),
        impuestos_trasladados=[
            ImpuestoTrasladado(
                impuesto="002",
                tasa=Decimal("0.160000"),
                importe=subtotal * Decimal("0.16"),
                base=subtotal,
            )
        ],
        impuestos_retenidos=[],
        estado="vigente",
    )


def make_cfdi_pago(
    uuid: str = "uuid-pago-001",
    uuid_docto: str = "uuid-ppd-001",
    monto_pagado: Decimal = Decimal("11600"),
    objeto_imp_dr: str = "02",
    tasa_iva_dr: Decimal = Decimal("0.160000"),
    fecha_emision: str = "2025-01-20",
    isr_retenido_dr: Decimal = Decimal("0"),
    iva_retenido_dr: Decimal = Decimal("0"),
) -> CfdiNormalizado:
    """Crea un CFDI tipo P (complemento de pago)."""
    imp_dr = []
    if objeto_imp_dr == "02":
        imp_dr.append(
            ImpuestoDR(
                impuesto_dr="002",
                tasa_dr=tasa_iva_dr,
                importe_dr=monto_pagado - monto_pagado / (Decimal("1") + tasa_iva_dr),
                tipo="traslado",
            )
        )
    if isr_retenido_dr > Decimal("0"):
        imp_dr.append(
            ImpuestoDR(
                impuesto_dr="001",
                tasa_dr=Decimal("0.0125"),
                importe_dr=isr_retenido_dr,
                tipo="retencion",
            )
        )
    if iva_retenido_dr > Decimal("0"):
        imp_dr.append(
            ImpuestoDR(
                impuesto_dr="002",
                tasa_dr=Decimal("0.106667"),
                importe_dr=iva_retenido_dr,
                tipo="retencion",
            )
        )

    complemento = ComplementoPago(
        doctos_relacionados=[
            DoctoRelacionado(
                uuid_docto=uuid_docto,
                monto_pagado=monto_pagado,
                objeto_imp_dr=objeto_imp_dr,
                imp_dr=imp_dr,
            )
        ]
    )

    return CfdiNormalizado(
        uuid=uuid,
        tipo="P",
        metodo_pago="PPD",
        fecha_emision=fecha_emision,
        fecha_pago=fecha_emision,
        rfc_emisor="XAXX010101000",
        rfc_receptor="XAXX010101001",
        subtotal=Decimal("0"),
        total=Decimal("0"),
        impuestos_trasladados=[],
        impuestos_retenidos=[],
        estado="vigente",
        complemento_pago=complemento,
    )
