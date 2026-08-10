"""Shared fixtures for cfdi-parser tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def ingreso_pue_xml() -> bytes:
    return (FIXTURES_DIR / "ingreso_pue.xml").read_bytes()


@pytest.fixture
def ingreso_ppd_xml() -> bytes:
    return (FIXTURES_DIR / "ingreso_ppd.xml").read_bytes()


@pytest.fixture
def pago_20_xml() -> bytes:
    return (FIXTURES_DIR / "pago_20.xml").read_bytes()


@pytest.fixture
def retencion_11_xml() -> bytes:
    return (FIXTURES_DIR / "retencion_11.xml").read_bytes()


@pytest.fixture
def nomina_12_xml() -> bytes:
    return (FIXTURES_DIR / "nomina_12.xml").read_bytes()
