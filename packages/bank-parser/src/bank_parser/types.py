"""Tipos de datos para el parser de estados de cuenta bancarios.

IMPORTANTE: El estado de cuenta bancario NO es fuente de calculo fiscal.
Es una capa de conciliacion que sirve para:
  1. Detectar ingreso cobrado sin CFDI emitido (riesgo de omision)
  2. Acreditar "efectivamente pagado" para IVA acreditable
  3. Cerrar complementos de pago pendientes (PPD)

Si los montos bancarios se suman a los montos de CFDI, el ingreso se DUPLICA.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal
from typing import Optional


class NivelConfianza(enum.Enum):
    """Nivel de confianza en un dato parseado."""

    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"
    NO_CONFIABLE = "no_confiable"


@dataclass
class Movimiento:
    """Un movimiento individual en el estado de cuenta.

    Los montos usan signo: positivo = abono (credit), negativo = cargo (debit).
    """

    fecha: date
    hora: Optional[time]
    descripcion: str
    identificador_transaccion: str
    monto: Decimal
    comision: Decimal
    moneda: str
    detalle: dict = field(default_factory=dict)
    es_espejo: bool = False
    categoria: Optional[str] = None
    confianza: NivelConfianza = NivelConfianza.ALTA


@dataclass
class ExtractoBancario:
    """Resultado completo del parseo de un estado de cuenta bancario.

    Contiene los datos declarados por el banco, los movimientos parseados,
    y las validaciones cruzadas realizadas.
    """

    institucion: str
    titular: str  # Enmascarado
    identificador_cuenta: str  # Enmascarado
    periodo_inicio: date
    periodo_fin: date
    saldo_inicial: Decimal
    saldo_final: Decimal
    total_abonos_declarado: Decimal
    total_cargos_declarado: Decimal
    comisiones_declaradas: Decimal
    movimientos: list[Movimiento] = field(default_factory=list)
    es_confiable: bool = True
    alertas: list[str] = field(default_factory=list)
    pares_espejo: list[tuple[int, int]] = field(default_factory=list)

    @property
    def abono_neto(self) -> Decimal:
        """Suma de abonos excluyendo movimientos espejo."""
        return sum(
            (m.monto for m in self.movimientos if m.monto > 0 and not m.es_espejo),
            Decimal("0"),
        )

    @property
    def cargo_neto(self) -> Decimal:
        """Suma de cargos excluyendo movimientos espejo."""
        return sum(
            (m.monto for m in self.movimientos if m.monto < 0 and not m.es_espejo),
            Decimal("0"),
        )
