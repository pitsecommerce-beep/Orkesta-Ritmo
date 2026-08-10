"""Adaptador para estados de cuenta de Revolut."""

from __future__ import annotations

from pathlib import Path

from bank_parser.types import ExtractoBancario


class RevolutAdapter:
    """Adaptador para parsear estados de cuenta de Revolut."""

    institucion: str = "Revolut"

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a un estado de cuenta Revolut."""
        return False

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parsea un PDF de estado de cuenta Revolut."""
        raise NotImplementedError(
            "Adaptador de Revolut pendiente de implementacion"
        )
