"""Auto-deteccion de institucion bancaria a partir del texto del PDF.

Soporta dos estrategias:
1. Extraccion de texto via pdfplumber (PDFs con capa de texto)
2. OCR via tesseract (PDFs rasterizados como los de Santander)

Si pdfplumber no extrae texto significativo (< 50 chars), se intenta
OCR de la primera pagina a baja resolucion como sonda rapida.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

from bank_parser.adapters import TODOS_LOS_ADAPTADORES
from bank_parser.base import BankAdapter
from bank_parser.types import ExtractoBancario

logger = logging.getLogger(__name__)

_MIN_CHARS_TEXTO = 50


def _extrae_texto_pdf(path: Path) -> str:
    """Extrae el texto completo de un PDF usando pdfplumber."""
    with pdfplumber.open(path) as pdf:
        paginas = []
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                paginas.append(texto)
        return "\n".join(paginas)


def _extrae_texto_ocr(path: Path) -> str:
    """OCR the first page at low DPI for fast bank detection."""
    try:
        from bank_parser.ocr import ocr_primera_pagina
        return ocr_primera_pagina(path, dpi=200)
    except ImportError:
        logger.warning(
            "pytesseract o pdf2image no disponibles. "
            "No se puede detectar banco en PDFs rasterizados."
        )
        return ""
    except Exception:
        logger.exception("Error en OCR de primera pagina para deteccion")
        return ""


def detecta_institucion(path: Path) -> BankAdapter:
    """Detecta la institucion bancaria del PDF y retorna su adaptador.

    Intenta cada adaptador registrado en orden y retorna el primero
    cuyo metodo detecta() retorne True. Si el PDF no tiene capa de
    texto (rasterizado), usa OCR como fallback.

    Args:
        path: Ruta al archivo PDF del estado de cuenta.

    Returns:
        El adaptador correspondiente a la institucion detectada.

    Raises:
        ValueError: Si ningun adaptador reconoce el documento.
    """
    texto = _extrae_texto_pdf(path)

    if len(texto.strip()) < _MIN_CHARS_TEXTO:
        logger.info(
            "PDF sin texto extraible (%d chars). Intentando OCR para deteccion.",
            len(texto.strip()),
        )
        texto = _extrae_texto_ocr(path)

    if not texto.strip():
        raise ValueError(
            "No se pudo extraer texto del documento, ni por pdfplumber ni por OCR. "
            "Verifique que el archivo sea un PDF valido de estado de cuenta bancario. "
            "Si es un PDF rasterizado, asegurese de que tesseract-ocr este instalado."
        )

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
