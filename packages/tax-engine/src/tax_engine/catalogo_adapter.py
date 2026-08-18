"""
Adaptador entre CatalogoNormativo y el motor de calculo.

Construye un Ejercicio resuelto para una fecha de causacion dada,
traduciendo las tarifas del catalogo versionado (TarifaTramo) al
formato que el motor ya consume (TramoResico / TramoArt96).

Tambien recolecta los IDs exactos de tarifas, reglas e indicadores
usados en la resolucion, necesarios para trazabilidad en
resolucion_calculo.

La fecha de causacion se deriva como el ultimo dia del periodo:
  - Mensual: ultimo dia del mes correspondiente.
  - Trimestral: ultimo dia del ultimo mes del trimestre.
Esto es coherente con cuando se causa la obligacion fiscal.
"""

from __future__ import annotations

import calendar
import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from tax_engine.catalogo import (
    CatalogoNormativo,
    Tarifa,
    TipoIndicador,
    TipoTarifa,
)
from tax_engine.types import Ejercicio, TramoArt96, TramoResico


@dataclass(frozen=True)
class MetadataResolucion:
    """IDs exactos de los elementos del catalogo usados en la resolucion."""
    fecha_causacion: datetime.date
    tarifa_resico_id: Optional[str] = None
    tarifa_art96_id: Optional[str] = None
    indicador_uma_id: Optional[str] = None
    reglas_usadas: list[dict] = field(default_factory=list)
    tarifas_usadas: list[dict] = field(default_factory=list)
    indicadores_usados: list[dict] = field(default_factory=list)


@dataclass
class EjercicioResuelto:
    """Ejercicio con metadata de trazabilidad."""
    ejercicio: Ejercicio
    metadata: MetadataResolucion


def fecha_causacion_de_periodo(
    ejercicio_year: int,
    periodo: int,
    trimestral: bool = False,
) -> datetime.date:
    """Deriva la fecha de causacion como el ultimo dia del periodo."""
    if trimestral:
        mes = periodo * 3
    else:
        mes = periodo
    if mes < 1 or mes > 12:
        raise ValueError(f"Periodo invalido: mes resultante {mes}")
    ultimo_dia = calendar.monthrange(ejercicio_year, mes)[1]
    return datetime.date(ejercicio_year, mes, ultimo_dia)


def _convertir_tarifa_resico(tarifa: Tarifa) -> list[TramoResico]:
    """Convierte TarifaTramo del catalogo a TramoResico del motor."""
    resultado = []
    for tramo in tarifa.tramos:
        resultado.append(TramoResico(
            limite_superior=tramo.limite_superior or Decimal("999999999"),
            tasa=tramo.tasa or tramo.porcentaje,
        ))
    return resultado


def _convertir_tarifa_art96(tarifa: Tarifa) -> list[TramoArt96]:
    """Convierte TarifaTramo del catalogo a TramoArt96 del motor."""
    resultado = []
    for tramo in tarifa.tramos:
        resultado.append(TramoArt96(
            limite_inferior=tramo.limite_inferior,
            limite_superior=tramo.limite_superior,
            cuota_fija=tramo.cuota_fija,
            porcentaje=tramo.porcentaje,
        ))
    return resultado


def resolver_ejercicio(
    catalogo: CatalogoNormativo,
    fecha_causacion: datetime.date,
) -> EjercicioResuelto:
    """Construye un Ejercicio resuelto desde el catalogo para una fecha dada.

    Resuelve tarifas RESICO PF, Art. 96 y UMA mensual vigentes en la
    fecha de causacion.  Si alguna tarifa no existe para esa fecha (por
    ejemplo RESICO PF para 2024), se deja vacia — el motor validara
    segun el regimen del contribuyente.
    """
    tarifas_resico: list[TramoResico] = []
    tarifas_art96: list[TramoArt96] = []
    tarifa_resico_id: Optional[str] = None
    tarifa_art96_id: Optional[str] = None
    tarifas_usadas: list[dict] = []
    indicadores_usados: list[dict] = []

    # RESICO PF
    try:
        tarifa_resico = catalogo.resolver_tarifa(
            TipoTarifa.RESICO_PF_MENSUAL, fecha_causacion,
        )
        tarifas_resico = _convertir_tarifa_resico(tarifa_resico)
        tarifa_resico_id = tarifa_resico.id
        tarifas_usadas.append({
            "tarifa_id": tarifa_resico.id,
            "tipo": tarifa_resico.tipo.value,
            "norma_fuente_id": tarifa_resico.norma_fuente_id,
        })
    except Exception:
        pass

    # Art. 96
    try:
        tarifa_art96 = catalogo.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL, fecha_causacion,
        )
        tarifas_art96 = _convertir_tarifa_art96(tarifa_art96)
        tarifa_art96_id = tarifa_art96.id
        tarifas_usadas.append({
            "tarifa_id": tarifa_art96.id,
            "tipo": tarifa_art96.tipo.value,
            "norma_fuente_id": tarifa_art96.norma_fuente_id,
        })
    except Exception:
        pass

    # UMA mensual
    indicador_uma = catalogo.resolver_indicador(
        TipoIndicador.UMA_DIARIA, fecha_causacion,
    )
    uma_mensual = indicador_uma.valor * Decimal("30.4")
    indicadores_usados.append({
        "indicador_id": indicador_uma.id,
        "tipo": indicador_uma.tipo.value,
        "valor": str(indicador_uma.valor),
        "norma_fuente_id": indicador_uma.norma_fuente_id,
    })

    ejercicio = Ejercicio(
        year=fecha_causacion.year,
        umas_mensuales=uma_mensual,
        tarifas_resico=tarifas_resico,
        tarifas_art96=tarifas_art96,
    )

    metadata = MetadataResolucion(
        fecha_causacion=fecha_causacion,
        tarifa_resico_id=tarifa_resico_id,
        tarifa_art96_id=tarifa_art96_id,
        indicador_uma_id=indicador_uma.id,
        tarifas_usadas=tarifas_usadas,
        indicadores_usados=indicadores_usados,
    )

    return EjercicioResuelto(ejercicio=ejercicio, metadata=metadata)
