"""Type definitions for CFDI parsing.

All monetary values use Decimal to preserve exact precision required
by Mexican tax law (SAT).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Union


# ---------------------------------------------------------------------------
# CFDI Ingreso 4.0
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImpuestoConcepto:
    """A single tax line within a Concepto."""

    base: Decimal
    impuesto: str          # "002" = IVA, "001" = ISR, "003" = IEPS
    tipo_factor: str       # Tasa, Cuota, Exento
    tasa_o_cuota: Decimal
    importe: Decimal
    tipo: Literal["traslado", "retencion"]


@dataclass(frozen=True)
class Concepto:
    """A line item (concepto) within a CFDI Ingreso."""

    clave_prod_serv: str
    cantidad: Decimal
    descripcion: str
    valor_unitario: Decimal
    importe: Decimal
    objeto_imp: str        # "01" No objeto, "02" Si objeto, "03" Si objeto no obligado
    impuestos: list[ImpuestoConcepto] = field(default_factory=list)


@dataclass(frozen=True)
class ImpuestoTotal:
    """A summarised tax total at the Comprobante > Impuestos level."""

    base: Decimal
    impuesto: str
    tipo_factor: str
    tasa_o_cuota: Decimal
    importe: Decimal


@dataclass(frozen=True)
class CfdiIngreso:
    """Parsed representation of a CFDI 4.0 Comprobante de Ingreso."""

    version: str
    uuid: str
    serie: str
    folio: str
    fecha: datetime
    forma_pago: str
    metodo_pago: str       # PUE or PPD
    moneda: str
    tipo_cambio: Decimal
    subtotal: Decimal
    total: Decimal
    tipo_comprobante: str  # "I" for Ingreso
    rfc_emisor: str
    nombre_emisor: str
    regimen_emisor: str
    rfc_receptor: str
    nombre_receptor: str
    uso_cfdi: str
    conceptos: list[Concepto] = field(default_factory=list)
    impuestos_trasladados: list[ImpuestoTotal] = field(default_factory=list)
    impuestos_retenidos: list[ImpuestoTotal] = field(default_factory=list)
    objeto_imp: str = "02"
    estado: Literal["vigente", "cancelado", "pendiente_complemento"] = "vigente"


# ---------------------------------------------------------------------------
# Complemento de Pago 2.0
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImpuestoDR:
    """Tax detail at DoctoRelacionado level (Pagos 2.0)."""

    base_dr: Decimal
    impuesto_dr: str       # "002" IVA, "001" ISR, "003" IEPS
    tipo_factor_dr: str    # Tasa, Cuota, Exento
    tasa_o_cuota_dr: Decimal
    importe_dr: Decimal
    tipo: Literal["traslado", "retencion"]


@dataclass(frozen=True)
class DoctoRelacionado:
    """A document referenced by a payment (Pagos 2.0)."""

    id_documento: str      # UUID of the original CFDI
    serie: str
    folio: str
    moneda: str
    equivalencia: Decimal
    num_parcialidad: int
    imp_saldo_ant: Decimal
    imp_pagado: Decimal
    imp_saldo_insoluto: Decimal
    objeto_imp_dr: str
    impuestos_dr: list[ImpuestoDR] = field(default_factory=list)


@dataclass(frozen=True)
class Pago20:
    """A single payment within Complemento de Pago 2.0."""

    fecha_pago: datetime
    forma_pago: str
    monto: Decimal
    moneda: str
    tipo_cambio: Decimal
    doctos_relacionados: list[DoctoRelacionado] = field(default_factory=list)


@dataclass(frozen=True)
class TotalesPago20:
    """Optional Totales node in Complemento de Pago 2.0."""

    total_retenciones_iva: Decimal
    total_retenciones_isr: Decimal
    total_retenciones_ieps: Decimal
    total_traslados_base_iva16: Decimal
    total_traslados_impuesto_iva16: Decimal
    total_traslados_base_iva8: Decimal
    total_traslados_impuesto_iva8: Decimal
    total_traslados_base_iva0: Decimal
    total_traslados_impuesto_iva0: Decimal
    total_traslados_base_iva_exento: Decimal
    monto_total_pagos: Decimal


@dataclass(frozen=True)
class ComplementoPago20:
    """Parsed Complemento de Pago 2.0."""

    version: str
    totales: TotalesPago20 | None
    pagos: list[Pago20] = field(default_factory=list)


# ---------------------------------------------------------------------------
# CFDI Retenciones e Informacion de Pagos 1.1
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodoRetencion:
    """Fiscal period for a Retencion CFDI."""

    mes_ini: int
    mes_fin: int
    ejercicio: int


@dataclass(frozen=True)
class RetencionDetalle:
    """A single withholding tax detail line."""

    impuesto: str          # "001" ISR, "002" IVA, "003" IEPS
    monto_retenido: Decimal
    tipo_pago_ret: str     # Clave from c_TipoPagoRet catalogue


@dataclass(frozen=True)
class ComplementoPlataformas:
    """Optional complement for digital platform services."""

    version: str
    periodicidad: str
    numero_operacion: str
    monto_total_operacion: Decimal
    monto_total_retenido: Decimal


@dataclass(frozen=True)
class CfdiRetencion11:
    """Parsed CFDI Retenciones e Informacion de Pagos 1.1."""

    version: str
    uuid: str
    fecha: datetime
    rfc_emisor: str
    rfc_receptor: str
    periodo: PeriodoRetencion
    total_operacion: Decimal
    total_gravado: Decimal
    total_exento: Decimal
    total_retenido: Decimal
    retenciones: list[RetencionDetalle] = field(default_factory=list)
    complemento_plataformas: ComplementoPlataformas | None = None


# ---------------------------------------------------------------------------
# CFDI Nomina 1.2
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PercepcionDetalle:
    """A single perception (earning) line in a payroll CFDI."""

    tipo_percepcion: str
    clave: str
    concepto: str
    importe_gravado: Decimal
    importe_exento: Decimal


@dataclass(frozen=True)
class DeduccionDetalle:
    """A single deduction line in a payroll CFDI."""

    tipo_deduccion: str
    clave: str
    concepto: str
    importe: Decimal


@dataclass(frozen=True)
class CfdiNomina12:
    """Parsed CFDI Nomina 1.2 (payroll)."""

    version: str
    uuid: str
    fecha: datetime
    rfc_emisor: str
    rfc_receptor: str
    nombre_receptor: str
    total_percepciones: Decimal
    total_deducciones: Decimal
    total_otros_pagos: Decimal
    percepciones_detalle: list[PercepcionDetalle] = field(default_factory=list)
    deducciones_detalle: list[DeduccionDetalle] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Unified parse result
# ---------------------------------------------------------------------------

CfdiData = Union[CfdiIngreso, ComplementoPago20, CfdiRetencion11, CfdiNomina12]


@dataclass
class CfdiParseResult:
    """Unified result envelope returned by every parser."""

    tipo: Literal["ingreso", "pago", "retencion", "nomina"]
    data: CfdiData
    errores: list[str] = field(default_factory=list)
    es_valido: bool = True
