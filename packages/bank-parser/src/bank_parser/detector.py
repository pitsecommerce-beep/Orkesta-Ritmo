"""Auto-deteccion de institucion bancaria a partir del texto del PDF."""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from bank_parser.adapters import TODOS_LOS_ADAPTADORES
from bank_parser.base import BankAdapter
from bank_parser.types import ExtractoBancario


def _extrae_texto_pdf(path: Path) -> str:
    """Extrae el texto completo de un PDF usando pdfplumber."""
    with pdfplumber.open(path) as pdf:
        paginas = []
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                paginas.append(texto)
        return "\n".join(paginas)


def detecta_institucion(path: Path) -> BankAdapter:
    """Detecta la institucion bancaria del PDF y retorna su adaptador.

    Intenta cada adaptador registrado en orden y retorna el primero
    cuyo metodo detecta() retorne True.

    Args:
        path: Ruta al archivo PDF del estado de cuenta.

    Returns:
        El adaptador correspondiente a la institucion detectada.

    Raises:
        ValueError: Si ningun adaptador reconoce el documento.
    """
    texto = _extrae_texto_pdf(path)

    for adaptador in TODOS_LOS_ADAPTADORES:
        if adaptador.detecta(texto):
            return adaptador

    raise ValueError(
        "No se reconoce la institucion bancaria del documento. "
        "Instituciones soportadas: "
        + ", ".join(a.institucion for a in TODOS_LOS_ADAPTADORES)
    )


def parsea_estado_de_cuenta(path: Path) -> ExtractoBancario:
    """Detecta la institucion y parsea el estado de cuenta completo.

    Atajo que combina deteccion y parseo en una sola llamada.

    Args:
        path: Ruta al archivo PDF del estado de cuenta.

    Returns:
        El extracto bancario parseado.
    """
    adaptador = detecta_institucion(path)
    return adaptador.parsea(path)
