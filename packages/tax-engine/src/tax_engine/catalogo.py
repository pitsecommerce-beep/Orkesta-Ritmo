"""
Catalogo normativo versionado.

Modela reglas fiscales, tarifas, e indicadores con vigencia por rango de
fechas (no por ejercicio), jerarquia de fundamento legal, y estado de
confirmacion.  Resuelve la regla o tarifa vigente para una fecha de
causacion dada.

Principios de diseno:
- Vigencia por rango [vigencia_desde, vigencia_hasta).  vigencia_hasta=None
  significa "vigente sin fecha de termino conocida".
- Las tarifas del Anexo 8 corren por anio calendario completo (ene-dic).
  La UMA cambia el 1 de febrero, no el 1 de enero.
- Jerarquia de fundamento: base < sustituye < detalla < exime.
  Al resolver, gana la de mayor jerarquia vigente en la fecha de causacion.
- Decimal en todo, incluidos porcentajes.  El ultimo tramo de una tarifa
  tiene limite_superior=None, no un numero grande.
- Si no hay version vigente para la fecha, se levanta excepcion.
  Nunca se devuelve cero ni se estima con el ultimo valor conocido.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Optional

from tax_engine.exceptions import EjercicioNoDisponibleError


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TipoNorma(Enum):
    LEY = "LEY"
    RESOLUCION = "RESOLUCION"
    DECRETO = "DECRETO"
    LEY_INGRESOS = "LEY_INGRESOS"
    ANEXO_RMF = "ANEXO_RMF"
    DOF = "DOF"


class Jerarquia(IntEnum):
    BASE = 0
    SUSTITUYE = 1
    DETALLA = 2
    EXIME = 3


class EstadoConfirmacion(Enum):
    CONFIRMADO = "CONFIRMADO"
    NO_CONFIRMADO = "NO_CONFIRMADO"
    PENDIENTE_CONTADOR = "PENDIENTE_CONTADOR"


class TipoTarifa(Enum):
    ART96_MENSUAL = "ART96_MENSUAL"
    ART152_ANUAL = "ART152_ANUAL"
    ARRENDAMIENTO_MENSUAL = "ARRENDAMIENTO_MENSUAL"
    ARRENDAMIENTO_TRIMESTRAL = "ARRENDAMIENTO_TRIMESTRAL"
    RESICO_PF_MENSUAL = "RESICO_PF_MENSUAL"


class TipoIndicador(Enum):
    UMA_DIARIA = "UMA_DIARIA"
    UMA_MENSUAL = "UMA_MENSUAL"
    UMA_ANUAL = "UMA_ANUAL"
    INPC = "INPC"


# ---------------------------------------------------------------------------
# Norma fuente
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NormaFuente:
    """Documento publicado que fundamenta una regla."""
    id: str
    tipo: TipoNorma
    identificador: str
    fecha_publicacion_dof: datetime.date
    url: str = ""
    hash_pdf: str = ""
    descripcion: str = ""


# ---------------------------------------------------------------------------
# Regla fiscal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReglaFiscal:
    """Concepto estable con clave que nunca cambia."""
    clave: str
    descripcion: str
    regimen: str = ""


@dataclass
class ReglaVersion:
    """Valor concreto de una regla con vigencia y jerarquia."""
    id: str
    regla_clave: str
    valor: Decimal
    unidad: str = ""
    vigencia_desde: datetime.date = datetime.date(2000, 1, 1)
    vigencia_hasta: Optional[datetime.date] = None
    jerarquia: Jerarquia = Jerarquia.BASE
    norma_fuente_id: str = ""
    articulo: str = ""
    estado: EstadoConfirmacion = EstadoConfirmacion.CONFIRMADO
    nota_confirmacion: str = ""
    capturado_por: str = ""
    aprobado_por: str = ""


# ---------------------------------------------------------------------------
# Tarifa progresiva
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TarifaTramo:
    """Un tramo de una tarifa progresiva."""
    orden: int
    limite_inferior: Decimal
    limite_superior: Optional[Decimal]
    cuota_fija: Decimal
    porcentaje: Decimal  # Como porcentaje: 1.92 = 1.92%
    tasa: Optional[Decimal] = None  # Para RESICO: tasa directa


@dataclass
class Tarifa:
    """Tabla de tarifa progresiva con vigencia."""
    id: str
    tipo: TipoTarifa
    vigencia_desde: datetime.date
    vigencia_hasta: Optional[datetime.date] = None
    norma_fuente_id: str = ""
    articulo: str = ""
    estado: EstadoConfirmacion = EstadoConfirmacion.CONFIRMADO
    nota_confirmacion: str = ""
    tramos: list[TarifaTramo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Indicador economico
# ---------------------------------------------------------------------------

@dataclass
class Indicador:
    """Indicador economico con vigencia por rango de fechas."""
    id: str
    tipo: TipoIndicador
    valor: Decimal
    vigencia_desde: datetime.date
    vigencia_hasta: Optional[datetime.date] = None
    norma_fuente_id: str = ""
    estado: EstadoConfirmacion = EstadoConfirmacion.CONFIRMADO


# ---------------------------------------------------------------------------
# Catalogo: contenedor y resolucion
# ---------------------------------------------------------------------------

class CatalogoNormativo:
    """Contenedor de reglas, tarifas e indicadores con resolucion por fecha."""

    def __init__(self) -> None:
        self.normas: dict[str, NormaFuente] = {}
        self.reglas: dict[str, ReglaFiscal] = {}
        self.versiones: list[ReglaVersion] = []
        self.tarifas: list[Tarifa] = []
        self.indicadores: list[Indicador] = []

    def agregar_norma(self, norma: NormaFuente) -> None:
        self.normas[norma.id] = norma

    def agregar_regla(self, regla: ReglaFiscal) -> None:
        self.reglas[regla.clave] = regla

    def agregar_version(self, version: ReglaVersion) -> None:
        self.versiones.append(version)

    def agregar_tarifa(self, tarifa: Tarifa) -> None:
        self.tarifas.append(tarifa)

    def agregar_indicador(self, indicador: Indicador) -> None:
        self.indicadores.append(indicador)

    def _en_vigencia(
        self,
        fecha: datetime.date,
        desde: datetime.date,
        hasta: Optional[datetime.date],
    ) -> bool:
        if fecha < desde:
            return False
        if hasta is not None and fecha >= hasta:
            return False
        return True

    def resolver_regla(
        self,
        clave: str,
        fecha_causacion: datetime.date,
    ) -> ReglaVersion:
        """Resuelve la version vigente de mayor jerarquia para una fecha."""
        candidatas = [
            v for v in self.versiones
            if v.regla_clave == clave
            and self._en_vigencia(fecha_causacion, v.vigencia_desde, v.vigencia_hasta)
        ]
        if not candidatas:
            raise EjercicioNoDisponibleError(
                fecha_causacion.year,
                f"No hay version vigente de '{clave}' para {fecha_causacion}",
            )
        candidatas.sort(key=lambda v: v.jerarquia, reverse=True)
        return candidatas[0]

    def resolver_tarifa(
        self,
        tipo: TipoTarifa,
        fecha_causacion: datetime.date,
    ) -> Tarifa:
        """Resuelve la tarifa vigente para un tipo y fecha."""
        candidatas = [
            t for t in self.tarifas
            if t.tipo == tipo
            and self._en_vigencia(fecha_causacion, t.vigencia_desde, t.vigencia_hasta)
        ]
        if not candidatas:
            raise EjercicioNoDisponibleError(
                fecha_causacion.year,
                f"No hay tarifa '{tipo.value}' vigente para {fecha_causacion}",
            )
        return candidatas[0]

    def resolver_indicador(
        self,
        tipo: TipoIndicador,
        fecha_causacion: datetime.date,
    ) -> Indicador:
        """Resuelve el indicador vigente para un tipo y fecha."""
        candidatas = [
            i for i in self.indicadores
            if i.tipo == tipo
            and self._en_vigencia(fecha_causacion, i.vigencia_desde, i.vigencia_hasta)
        ]
        if not candidatas:
            raise EjercicioNoDisponibleError(
                fecha_causacion.year,
                f"No hay indicador '{tipo.value}' vigente para {fecha_causacion}",
            )
        return candidatas[0]

    def resolver_uma_diaria(self, fecha_causacion: datetime.date) -> Decimal:
        """Atajo: resuelve la UMA diaria vigente."""
        return self.resolver_indicador(TipoIndicador.UMA_DIARIA, fecha_causacion).valor

    def resolver_uma_mensual(self, fecha_causacion: datetime.date) -> Decimal:
        """Atajo: UMA mensual = UMA diaria * 30.4."""
        diaria = self.resolver_uma_diaria(fecha_causacion)
        return diaria * Decimal("30.4")
