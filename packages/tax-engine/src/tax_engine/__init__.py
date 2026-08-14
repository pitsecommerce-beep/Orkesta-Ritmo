"""
tax_engine - Motor de calculo fiscal para Orkesta Ritmo.

Calcula ISR e IVA para regimenes fiscales mexicanos:
- RESICO Persona Fisica
- RESICO Persona Fisica con Sueldos
- Arrendamiento
- Arrendamiento con Sueldos
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
from tax_engine.exceptions import EjercicioNoDisponibleError, RegimenEnValidacionError
from tax_engine.rfc import ResultadoRfc, validar_rfc
from tax_engine.tarifas_fallback import (
    obtener_ejercicio as obtener_ejercicio_fallback,
    buscar_tramo_resico,
    buscar_tramo_art96,
)

__all__ = [
    "calcular",
    "EjercicioNoDisponibleError",
    "RegimenEnValidacionError",
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
    "obtener_ejercicio_fallback",
    "buscar_tramo_resico",
    "buscar_tramo_art96",
    "ResultadoRfc",
    "validar_rfc",
]
