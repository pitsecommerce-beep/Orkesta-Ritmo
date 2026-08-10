"""Adaptador para estados de cuenta de Santander Mexico."""

from __future__ import annotations

from pathlib import Path

from bank_parser.types import ExtractoBancario


class SantanderAdapter:
    """Adaptador para parsear estados de cuenta de Santander Mexico."""

    institucion: str = "Santander"

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a un estado de cuenta Santander."""
        return False

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parsea un PDF de estado de cuenta Santander."""
        raise NotImplementedError(
            "Adaptador de Santander pendiente de implementacion"
        )
