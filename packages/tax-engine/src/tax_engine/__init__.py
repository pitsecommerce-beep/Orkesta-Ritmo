"""
tax_engine - Motor de calculo fiscal para Orkesta Ritmo.

Calcula ISR e IVA para regimenes fiscales mexicanos:
- RESICO Persona Fisica
- RESICO Persona Fisica con Sueldos
- Arrendamiento
- Arrendamiento con Sueldos
- RESICO Persona Moral
"""

from tax_engine.types import (
    CfdiNormalizado,
    ComplementoPago,
    DesgloseISR,
    DesgloseIVA,
    DoctoRelacionado,
    Ejercicio,
    ImpuestoDR,
    ImpuestoRetenido,
    ImpuestoTrasladado,
    PerfilFiscal,
    Regimen,
    ResultadoActividad,
    ResultadoCalculo,
    ResultadoClasificacion,
    TramoArt96,
    TramoResico,
    TrazabilidadCfdi,
)
from tax_engine.engine import calcular

__all__ = [
    "calcular",
    "CfdiNormalizado",
    "ComplementoPago",
    "DesgloseISR",
    "DesgloseIVA",
    "DoctoRelacionado",
    "Ejercicio",
    "ImpuestoDR",
    "ImpuestoRetenido",
    "ImpuestoTrasladado",
    "PerfilFiscal",
    "Regimen",
    "ResultadoActividad",
    "ResultadoCalculo",
    "ResultadoClasificacion",
    "TramoResico",
    "TramoArt96",
    "TrazabilidadCfdi",
]
