"""
Motor principal de calculo fiscal.

Funcion pura que recibe CFDIs normalizados, perfil fiscal y ejercicio.
Retorna ResultadoCalculo con trazabilidad completa a cada UUID.
No accede a base de datos, red, ni servicios externos.
"""

from decimal import Decimal
from typing import Optional

from tax_engine.arrendamiento import calcular_isr_arrendamiento
from tax_engine.clasificador import clasificar_cfdis
from tax_engine.iva import calcular_iva
from tax_engine.resico_pf import calcular_isr_resico_pf
from tax_engine.resico_pm import calcular_isr_resico_pm
from tax_engine.tarifas import obtener_ejercicio
from tax_engine.types import (
    CfdiNormalizado,
    DesgloseISR,
    DesgloseIVA,
    Ejercicio,
    PerfilFiscal,
    Regimen,
    ResultadoActividad,
    ResultadoCalculo,
)


def calcular(
    cfdis_emitidos: list[CfdiNormalizado],
    perfil: PerfilFiscal,
    ejercicio_year: int,
    periodo: int,
    clasificaciones_actividad: Optional[list[ResultadoActividad]] = None,
    cfdis_recibidos: Optional[list[CfdiNormalizado]] = None,
) -> ResultadoCalculo:
    """
    Calcula ISR e IVA para un periodo fiscal.

    Funcion pura: no accede a DB, red, ni AI.

    Args:
        cfdis_emitidos: CFDIs emitidos por el contribuyente en el periodo.
        perfil: Perfil fiscal del contribuyente.
        ejercicio_year: Year del ejercicio fiscal (ej: 2025).
        periodo: Numero de periodo (1-12 para mensual, 1-4 para trimestral).
        clasificaciones_actividad: Clasificacion de actividades para IVA.
        cfdis_recibidos: CFDIs de gastos recibidos para IVA acreditable.

    Returns:
        ResultadoCalculo con desglose de ISR, IVA, alertas y trazabilidad.

    Raises:
        ValueError: Si el ejercicio no tiene tarifas disponibles.
    """
    alertas: list[str] = []

    # Obtener datos del ejercicio
    ejercicio = obtener_ejercicio(ejercicio_year)
    if ejercicio is None:
        raise ValueError(
            f"Ejercicio fiscal {ejercicio_year} no disponible. "
            f"Solo se soportan ejercicios con tarifas cargadas."
        )

    # Validar que el ejercicio tenga tarifas
    if perfil.regimen in (Regimen.RESICO_PF, Regimen.RESICO_PF_SUELDOS, Regimen.RESICO_PM):
        if not ejercicio.tarifas_resico:
            raise ValueError(
                f"Ejercicio {ejercicio_year} no tiene tarifas RESICO cargadas."
            )
    elif perfil.regimen in (Regimen.ARRENDAMIENTO, Regimen.ARRENDAMIENTO_SUELDOS):
        if not ejercicio.tarifas_art96:
            raise ValueError(
                f"Ejercicio {ejercicio_year} no tiene tarifas Art. 96 cargadas."
            )

    # Clasificar CFDIs emitidos
    cfdis_clasificados = clasificar_cfdis(cfdis_emitidos)

    # Calcular ISR segun regimen
    if perfil.regimen in (Regimen.RESICO_PF, Regimen.RESICO_PF_SUELDOS):
        isr, alertas_isr = calcular_isr_resico_pf(
            cfdis_clasificados,
            ejercicio.tarifas_resico,
        )
    elif perfil.regimen in (Regimen.ARRENDAMIENTO, Regimen.ARRENDAMIENTO_SUELDOS):
        isr, alertas_isr = calcular_isr_arrendamiento(
            cfdis_clasificados,
            ejercicio.tarifas_art96,
            tipo_deduccion=perfil.tipo_deduccion,
            opcion_trimestral=perfil.opcion_trimestral,
        )
    elif perfil.regimen == Regimen.RESICO_PM:
        isr, alertas_isr = calcular_isr_resico_pm(
            cfdis_clasificados,
            ejercicio.tarifas_resico,
        )
    else:
        raise ValueError(f"Regimen no soportado: {perfil.regimen}")

    alertas.extend(alertas_isr)

    # Calcular IVA (comun a todos los regimenes)
    iva, alertas_iva = calcular_iva(
        cfdis_clasificados,
        clasificaciones_actividad=clasificaciones_actividad,
        cfdis_recibidos=cfdis_recibidos,
    )
    alertas.extend(alertas_iva)

    # Determinar estado
    estado = "calculado"
    if iva.requiere_revision:
        estado = "requiere_revision"
    if alertas:
        estado = "calculado_con_alertas"
    if iva.requiere_revision and alertas:
        estado = "requiere_revision"

    return ResultadoCalculo(
        periodo_ejercicio=ejercicio_year,
        periodo_numero=periodo,
        isr=isr,
        iva=iva,
        alertas=alertas,
        estado=estado,
    )
