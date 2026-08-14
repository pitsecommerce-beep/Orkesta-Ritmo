"""
Tipos de datos para el motor de calculo fiscal.

Todas las cantidades monetarias usan Decimal. Nunca float.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class Regimen(Enum):
    """Regimenes fiscales soportados."""
    RESICO_PF = "RESICO_PF"
    RESICO_PF_SUELDOS = "RESICO_PF_SUELDOS"
    ARRENDAMIENTO = "ARRENDAMIENTO"
    ARRENDAMIENTO_SUELDOS = "ARRENDAMIENTO_SUELDOS"
    RESICO_PM = "RESICO_PM"


class ResultadoClasificacion(Enum):
    """Resultado de la clasificacion de actividad para IVA."""
    IVA16 = "IVA16"
    IVA0 = "IVA0"
    EXENTO = "EXENTO"
    NO_APLICA = "NO_APLICA"
    SEPARAR = "SEPARAR"
    REVISAR = "REVISAR"


@dataclass
class ImpuestoTrasladado:
    """Impuesto trasladado en un CFDI."""
    impuesto: str  # "002" = IVA, "003" = IEPS
    tasa: Decimal
    importe: Decimal
    base: Decimal


@dataclass
class ImpuestoRetenido:
    """Impuesto retenido en un CFDI."""
    impuesto: str  # "001" = ISR, "002" = IVA
    tasa: Decimal
    importe: Decimal


@dataclass
class ImpuestoDR:
    """Impuesto en documento relacionado de complemento de pago."""
    impuesto_dr: str  # "001" = ISR, "002" = IVA
    tasa_dr: Decimal
    importe_dr: Decimal
    tipo: str  # "traslado" o "retencion"


@dataclass
class DoctoRelacionado:
    """Documento relacionado en un complemento de pago."""
    uuid_docto: str
    monto_pagado: Decimal
    objeto_imp_dr: str  # "01" = No objeto, "02" = Si objeto
    imp_dr: list[ImpuestoDR] = field(default_factory=list)


@dataclass
class ComplementoPago:
    """Complemento de pago (CFDI tipo P)."""
    doctos_relacionados: list[DoctoRelacionado] = field(default_factory=list)


@dataclass
class CfdiNormalizado:
    """CFDI normalizado con todos los campos relevantes para calculo fiscal."""
    uuid: str
    tipo: str  # "I" = Ingreso, "P" = Pago, "E" = Egreso, "N" = Nomina
    metodo_pago: str  # "PUE" o "PPD"
    fecha_emision: str  # ISO date string
    fecha_pago: Optional[str]  # ISO date string, opcional
    rfc_emisor: str
    rfc_receptor: str
    subtotal: Decimal
    total: Decimal
    impuestos_trasladados: list[ImpuestoTrasladado] = field(default_factory=list)
    impuestos_retenidos: list[ImpuestoRetenido] = field(default_factory=list)
    estado: str = "vigente"  # "vigente", "cancelado", "pendiente_complemento"
    objeto_imp: str = "02"  # "01" = No objeto, "02" = Si objeto
    actividad_id: Optional[str] = None
    tasa_iva: Optional[Decimal] = None
    complemento_pago: Optional[ComplementoPago] = None


@dataclass
class PerfilFiscal:
    """Perfil fiscal del contribuyente."""
    regimen: Regimen
    rfc: str
    tipo_deduccion: str = "opcional"
    presenta_anual: bool = False
    opcion_trimestral: bool = False


@dataclass
class ResultadoActividad:
    """Resultado de clasificacion de actividad."""
    actividad_id: str
    resultado: ResultadoClasificacion


@dataclass
class TrazabilidadCfdi:
    """Trazabilidad de un CFDI en el calculo."""
    uuid: str
    concepto: str
    monto: Decimal


@dataclass
class DesgloseISR:
    """Desglose del calculo de ISR."""
    ingresos: Decimal
    deducciones: Decimal
    base_gravable: Decimal
    impuesto_determinado: Decimal
    retenciones_isr: Decimal
    isr_a_cargo: Decimal
    trazabilidad: list[TrazabilidadCfdi] = field(default_factory=list)


@dataclass
class DesgloseIVA:
    """Desglose del calculo de IVA."""
    iva_trasladado: Decimal
    iva_retenido: Decimal
    iva_acreditable: Decimal
    iva_a_pagar: Decimal
    requiere_revision: bool = False
    motivo_revision: Optional[str] = None
    trazabilidad: list[TrazabilidadCfdi] = field(default_factory=list)


@dataclass
class TramoResico:
    """Tramo de la tarifa RESICO."""
    limite_superior: Decimal
    tasa: Decimal  # Porcentaje como Decimal, ej: Decimal("1.00") para 1%


@dataclass
class TramoArt96:
    """Tramo de la tarifa del Art. 96 LISR."""
    limite_inferior: Decimal
    limite_superior: Optional[Decimal]  # None para el ultimo tramo
    cuota_fija: Decimal
    porcentaje: Decimal  # Porcentaje como Decimal, ej: Decimal("1.92") para 1.92%


@dataclass
class Ejercicio:
    """Ejercicio fiscal con sus parametros."""
    year: int
    umas_mensuales: Decimal
    tarifas_resico: list[TramoResico] = field(default_factory=list)
    tarifas_art96: list[TramoArt96] = field(default_factory=list)


@dataclass
class ResultadoCalculo:
    """Resultado completo del calculo fiscal de un periodo."""
    periodo_ejercicio: int
    periodo_numero: int  # Mes (1-12) o trimestre (1-4)
    isr: DesgloseISR
    iva: DesgloseIVA
    alertas: list[str] = field(default_factory=list)
    estado: str = "calculado"
