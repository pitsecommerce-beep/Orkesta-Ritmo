"""
Sync-check: compares tarifas_fallback.py against the DB seed SQL.

If this test fails, someone updated one source without the other.
The DB (supabase/migrations/00003_seed_data.sql) is the source of truth;
update tarifas_fallback.py to match.

DB stores tasa/porcentaje as decimal fractions (0.0100 = 1%).
Python types use percentage notation (Decimal("1.00") = 1%).
"""

import re
from decimal import Decimal
from pathlib import Path

import pytest

from tax_engine.tarifas_fallback import obtener_ejercicio

SEED_SQL = Path(__file__).resolve().parents[3] / "supabase" / "migrations" / "00003_seed_data.sql"


def _parse_resico_seed(sql: str) -> list[dict]:
    rows = []
    pattern = re.compile(
        r"\('a0000000-0000-0000-0000-000000002025',\s*"
        r"([\d.]+),\s*([\d.]+),\s*(\d+)\)"
    )
    in_resico = False
    for line in sql.splitlines():
        if "INSERT INTO tarifas_resico" in line:
            in_resico = True
        if in_resico:
            for m in pattern.finditer(line):
                rows.append({
                    "limite_superior": Decimal(m.group(1)),
                    "tasa_fraction": Decimal(m.group(2)),
                    "orden": int(m.group(3)),
                })
        if in_resico and ";" in line:
            in_resico = False
    return sorted(rows, key=lambda r: r["orden"])


def _parse_art96_seed(sql: str) -> list[dict]:
    rows = []
    pattern = re.compile(
        r"\('a0000000-0000-0000-0000-000000002025',\s*"
        r"([\d.]+),\s*([\w.]+),\s*([\d.]+),\s*([\d.]+),\s*(\d+)\)"
    )
    in_art96 = False
    for line in sql.splitlines():
        if "INSERT INTO tarifas_art96" in line:
            in_art96 = True
        if in_art96:
            for m in pattern.finditer(line):
                lim_sup = None if m.group(2) == "NULL" else Decimal(m.group(2))
                rows.append({
                    "limite_inferior": Decimal(m.group(1)),
                    "limite_superior": lim_sup,
                    "cuota_fija": Decimal(m.group(3)),
                    "porcentaje_fraction": Decimal(m.group(4)),
                    "orden": int(m.group(5)),
                })
        if in_art96 and ";" in line:
            in_art96 = False
    return sorted(rows, key=lambda r: r["orden"])


@pytest.fixture
def seed_sql() -> str:
    return SEED_SQL.read_text()


class TestResicoParity:
    def test_same_number_of_tramos(self, seed_sql):
        ej = obtener_ejercicio(2025)
        assert ej is not None
        seed_rows = _parse_resico_seed(seed_sql)
        assert len(seed_rows) == len(ej.tarifas_resico), (
            f"Seed has {len(seed_rows)} RESICO rows, fallback has {len(ej.tarifas_resico)}"
        )

    def test_limite_superior_matches(self, seed_sql):
        ej = obtener_ejercicio(2025)
        seed_rows = _parse_resico_seed(seed_sql)
        for seed_row, fb_tramo in zip(seed_rows, ej.tarifas_resico):
            assert seed_row["limite_superior"] == fb_tramo.limite_superior, (
                f"Orden {seed_row['orden']}: seed={seed_row['limite_superior']} "
                f"vs fallback={fb_tramo.limite_superior}"
            )

    def test_tasa_matches_after_conversion(self, seed_sql):
        ej = obtener_ejercicio(2025)
        seed_rows = _parse_resico_seed(seed_sql)
        for seed_row, fb_tramo in zip(seed_rows, ej.tarifas_resico):
            seed_pct = seed_row["tasa_fraction"] * 100
            assert seed_pct == fb_tramo.tasa, (
                f"Orden {seed_row['orden']}: seed fraction {seed_row['tasa_fraction']} "
                f"-> {seed_pct}% vs fallback {fb_tramo.tasa}%"
            )


class TestArt96Parity:
    def test_same_number_of_tramos(self, seed_sql):
        ej = obtener_ejercicio(2025)
        assert ej is not None
        seed_rows = _parse_art96_seed(seed_sql)
        assert len(seed_rows) == len(ej.tarifas_art96), (
            f"Seed has {len(seed_rows)} Art96 rows, fallback has {len(ej.tarifas_art96)}"
        )

    def test_limites_match(self, seed_sql):
        ej = obtener_ejercicio(2025)
        seed_rows = _parse_art96_seed(seed_sql)
        for seed_row, fb_tramo in zip(seed_rows, ej.tarifas_art96):
            assert seed_row["limite_inferior"] == fb_tramo.limite_inferior, (
                f"Orden {seed_row['orden']}: lim_inf seed={seed_row['limite_inferior']} "
                f"vs fallback={fb_tramo.limite_inferior}"
            )
            assert seed_row["limite_superior"] == fb_tramo.limite_superior, (
                f"Orden {seed_row['orden']}: lim_sup seed={seed_row['limite_superior']} "
                f"vs fallback={fb_tramo.limite_superior}"
            )

    def test_cuota_fija_matches(self, seed_sql):
        ej = obtener_ejercicio(2025)
        seed_rows = _parse_art96_seed(seed_sql)
        for seed_row, fb_tramo in zip(seed_rows, ej.tarifas_art96):
            assert seed_row["cuota_fija"] == fb_tramo.cuota_fija, (
                f"Orden {seed_row['orden']}: cuota seed={seed_row['cuota_fija']} "
                f"vs fallback={fb_tramo.cuota_fija}"
            )

    def test_porcentaje_matches_after_conversion(self, seed_sql):
        ej = obtener_ejercicio(2025)
        seed_rows = _parse_art96_seed(seed_sql)
        for seed_row, fb_tramo in zip(seed_rows, ej.tarifas_art96):
            seed_pct = seed_row["porcentaje_fraction"] * 100
            assert seed_pct == fb_tramo.porcentaje, (
                f"Orden {seed_row['orden']}: seed fraction {seed_row['porcentaje_fraction']} "
                f"-> {seed_pct}% vs fallback {fb_tramo.porcentaje}%"
            )
