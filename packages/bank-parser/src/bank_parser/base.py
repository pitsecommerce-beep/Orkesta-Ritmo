"""Protocolo base para adaptadores de bancos."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from bank_parser.types import ExtractoBancario


@runtime_checkable
class BankAdapter(Protocol):
    """Protocolo que deben cumplir todos los adaptadores bancarios.

    Cada adaptador sabe detectar si un texto proviene de su institucion
    y parsear el PDF completo a un ExtractoBancario.
    """

    institucion: str

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a esta institucion."""
        ...

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parsea un PDF de estado de cuenta y retorna un ExtractoBancario."""
        ...
