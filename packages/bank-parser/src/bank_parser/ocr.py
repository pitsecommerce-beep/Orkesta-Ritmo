"""OCR utilities for rasterized PDF bank statements.

Santander (and potentially other banks) deliver statements as rasterized
PDFs with zero extractable text. This module wraps tesseract via
pytesseract + pdf2image to produce per-page text from such documents.

Design decisions documented here:
- psm 4 is the default for movement tables because psm 6 silently drops
  rows (verified empirically on real Santander statements).
- DPI 300 balances accuracy vs speed. Lower DPI degrades small-font
  amounts; higher DPI yields negligible improvement.
- Language spa is required for accent-correct descriptions but eng-only
  still reads amounts and dates correctly.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def ocr_paginas(
    path: Path,
    *,
    dpi: int = 300,
    lang: str = "spa",
    psm: int = 4,
) -> list[str]:
    """Return OCR text for each page of a rasterized PDF."""
    images = convert_from_path(str(path), dpi=dpi)
    results: list[str] = []
    config = f"--psm {psm}"
    for img in images:
        text = pytesseract.image_to_string(img, lang=lang, config=config)
        results.append(text)
    return results


def ocr_primera_pagina(
    path: Path,
    *,
    dpi: int = 200,
    lang: str = "spa",
    psm: int = 4,
) -> str:
    """OCR only the first page at lower DPI — fast detection probe."""
    images = convert_from_path(str(path), dpi=dpi, first_page=1, last_page=1)
    if not images:
        return ""
    return pytesseract.image_to_string(images[0], lang=lang, config=f"--psm {psm}")


def normalizar_texto(texto: str) -> str:
    """Normalize text for fuzzy anchor matching.

    Strips accents, uppercases, collapses whitespace. This lets OCR output
    like 'DESCRIPCION' match the PDF's 'DESCRIPCIÓN'.
    """
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(sin_acentos.upper().split())
