"""Fixtures compartidas para tests del bank-parser."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mercado_pago_sample_path() -> Path:
    """Ruta al archivo de fixture de Mercado Pago."""
    return FIXTURES_DIR / "mercado_pago_sintetico.txt"


@pytest.fixture
def mercado_pago_sample_text(mercado_pago_sample_path: Path) -> str:
    """Texto completo del fixture de Mercado Pago."""
    return mercado_pago_sample_path.read_text(encoding="utf-8")
