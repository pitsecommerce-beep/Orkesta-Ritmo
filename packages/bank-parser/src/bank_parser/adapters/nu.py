"""Adaptador para estados de cuenta de Nu Mexico."""

from __future__ import annotations

from pathlib import Path

from bank_parser.types import ExtractoBancario


class NuAdapter:
    """Adaptador para parsear estados de cuenta de Nu Mexico."""

    institucion: str = "Nu"

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a un estado de cuenta Nu."""
        return False

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parsea un PDF de estado de cuenta Nu."""
        raise NotImplementedError("Adaptador de Nu pendiente de implementacion")
