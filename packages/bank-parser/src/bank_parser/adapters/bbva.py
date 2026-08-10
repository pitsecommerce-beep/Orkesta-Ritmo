"""Adaptador para estados de cuenta de BBVA Mexico."""

from __future__ import annotations

from pathlib import Path

from bank_parser.types import ExtractoBancario


class BBVAAdapter:
    """Adaptador para parsear estados de cuenta de BBVA Mexico."""

    institucion: str = "BBVA"

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a un estado de cuenta BBVA."""
        return False

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parsea un PDF de estado de cuenta BBVA."""
        raise NotImplementedError("Adaptador de BBVA pendiente de implementacion")
