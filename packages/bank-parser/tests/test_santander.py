"""Tests for Santander bank statement adapter.

Tests run against RASTERIZED PDFs (the acceptance fixtures) to validate
the full OCR pipeline. Text-based PDFs exist only for fast debugging.

Expected values come from the fixture generator (gen_santander_dummy.py):
- Debito: saldo_inicial=1000, depositos=8300.50, retiros=4300.50, saldo_final=5000
- Credito: total_cargos=4500, total_abonos=3000, 5 cargos + 1 abono
"""

import re
from unittest.mock import patch

import pytest
from decimal import Decimal
from pathlib import Path

from bank_parser.adapters.santander import (
    SantanderAdapter,
    _parse_monto,
    _parse_fecha_ddmmmyyyy,
    _validar_cuadre_debito,
    _validar_cuadre_credito,
    _ResumenDebito,
)
from bank_parser.detector import detecta_institucion, parsea_estado_de_cuenta
from bank_parser.ocr import ocr_paginas
from bank_parser.types import Movimiento, NivelConfianza

FIXTURES = Path(__file__).parent / "fixtures"
DEBITO_RASTER = FIXTURES / "santander_debito_RASTERIZADO.pdf"
CREDITO_RASTER = FIXTURES / "santander_credito_RASTERIZADO.pdf"
DEBITO_TEXTO = FIXTURES / "santander_debito_TEXTO.pdf"
CREDITO_TEXTO = FIXTURES / "santander_credito_TEXTO.pdf"


@pytest.fixture
def adapter():
    return SantanderAdapter()


# ─── Detection ───────────────────────────────────────────────────────


class TestDeteccion:
    def test_detecta_santander_debito_rasterizado(self):
        ad = detecta_institucion(DEBITO_RASTER)
        assert ad.institucion == "Santander"

    def test_detecta_santander_credito_rasterizado(self):
        ad = detecta_institucion(CREDITO_RASTER)
        assert ad.institucion == "Santander"

    def test_detecta_producto_debito(self, adapter):
        from bank_parser.ocr import ocr_paginas
        paginas = ocr_paginas(DEBITO_RASTER)
        assert adapter.detecta_producto(paginas) == "debito"

    def test_detecta_producto_credito(self, adapter):
        from bank_parser.ocr import ocr_paginas
        paginas = ocr_paginas(CREDITO_RASTER)
        assert adapter.detecta_producto(paginas) == "credito"

    def test_detecta_texto_santander(self, adapter):
        assert adapter.detecta("Santander ESTADO DE CUENTA") is True
        assert adapter.detecta("BANCO SANTANDER MEXICO") is True
        assert adapter.detecta("Banco random de Mexico") is False
        assert adapter.detecta("") is False


# ─── Debito ──────────────────────────────────────────────────────────


class TestDebitoRasterizado:
    @pytest.fixture(autouse=True)
    def setup(self, adapter):
        self.extracto = adapter.parsea(DEBITO_RASTER)

    def test_institucion(self):
        assert self.extracto.institucion == "Santander"

    def test_titular(self):
        assert "PEREZ" in self.extracto.titular or "SINTETICO" in self.extracto.titular

    def test_cuenta(self):
        assert self.extracto.identificador_cuenta != ""

    def test_periodo(self):
        from datetime import date
        assert self.extracto.periodo_inicio == date(2025, 12, 1)
        assert self.extracto.periodo_fin == date(2025, 12, 31)

    def test_saldo_inicial(self):
        assert self.extracto.saldo_inicial == Decimal("1000.00")

    def test_saldo_final(self):
        assert self.extracto.saldo_final == Decimal("5000.00")

    def test_depositos_declarados(self):
        assert self.extracto.total_abonos_declarado == Decimal("8300.50")

    def test_retiros_declarados(self):
        assert self.extracto.total_cargos_declarado == Decimal("4300.50")

    def test_cantidad_movimientos(self):
        assert len(self.extracto.movimientos) == 6

    def test_cuadre(self):
        assert self.extracto.es_confiable is True
        assert self.extracto.alertas == []

    def test_cuadre_aritmetico(self):
        sum_dep = sum(m.monto for m in self.extracto.movimientos if m.monto > 0)
        sum_ret = abs(sum(m.monto for m in self.extracto.movimientos if m.monto < 0))
        assert sum_dep == Decimal("8300.50")
        assert sum_ret == Decimal("4300.50")
        assert self.extracto.saldo_inicial + sum_dep - sum_ret == self.extracto.saldo_final

    def test_rfc_extraido(self):
        rfcs = [m.detalle.get("rfc") for m in self.extracto.movimientos if m.detalle.get("rfc")]
        assert "XAXX010101000" in rfcs
        assert "XEXX010101000" in rfcs

    def test_montos_son_decimal(self):
        for m in self.extracto.movimientos:
            assert isinstance(m.monto, Decimal)

    def test_movimientos_individuales(self):
        movs = self.extracto.movimientos
        assert movs[0].monto == Decimal("5000.00")
        assert movs[1].monto == Decimal("-1500.00")
        assert movs[2].monto == Decimal("2300.50")
        assert movs[3].monto == Decimal("-800.50")
        assert movs[4].monto == Decimal("1000.00")
        assert movs[5].monto == Decimal("-2000.00")


# ─── Credito ─────────────────────────────────────────────────────────


class TestCreditoRasterizado:
    @pytest.fixture(autouse=True)
    def setup(self, adapter):
        self.extracto = adapter.parsea(CREDITO_RASTER)

    def test_institucion(self):
        assert self.extracto.institucion == "Santander"

    def test_titular(self):
        assert "PEREZ" in self.extracto.titular or "SINTETICO" in self.extracto.titular

    def test_periodo(self):
        from datetime import date
        assert self.extracto.periodo_inicio == date(2025, 11, 13)
        assert self.extracto.periodo_fin == date(2025, 12, 12)

    def test_total_cargos(self):
        assert self.extracto.total_cargos_declarado == Decimal("4500.00")

    def test_total_abonos(self):
        assert self.extracto.total_abonos_declarado == Decimal("3000.00")

    def test_cantidad_movimientos(self):
        assert len(self.extracto.movimientos) == 6

    def test_cargos_vs_abonos(self):
        cargos = [m for m in self.extracto.movimientos if m.monto > 0]
        abonos = [m for m in self.extracto.movimientos if m.monto < 0]
        assert len(cargos) == 5
        assert len(abonos) == 1

    def test_cuadre(self):
        assert self.extracto.es_confiable is True
        assert self.extracto.alertas == []

    def test_cuadre_aritmetico(self):
        sum_cargos = sum(m.monto for m in self.extracto.movimientos if m.monto > 0)
        sum_abonos = abs(sum(m.monto for m in self.extracto.movimientos if m.monto < 0))
        assert sum_cargos == Decimal("4500.00")
        assert sum_abonos == Decimal("3000.00")

    def test_montos_son_decimal(self):
        for m in self.extracto.movimientos:
            assert isinstance(m.monto, Decimal)


# ─── Validacion de cuadre ────────────────────────────────────────────


class TestValidacionCuadre:
    def test_debito_cuadra(self):
        from datetime import date
        movimientos = [
            Movimiento(
                fecha=date(2025, 12, 4), hora=None,
                descripcion="dep", identificador_transaccion="1",
                monto=Decimal("5000"), comision=Decimal("0"),
                moneda="MXN",
            ),
            Movimiento(
                fecha=date(2025, 12, 5), hora=None,
                descripcion="ret", identificador_transaccion="2",
                monto=Decimal("-1500"), comision=Decimal("0"),
                moneda="MXN",
            ),
        ]
        resumen = _ResumenDebito(
            saldo_inicial=Decimal("1000"),
            depositos_declarados=Decimal("5000"),
            retiros_declarados=Decimal("1500"),
            saldo_final=Decimal("4500"),
        )
        ok, alertas = _validar_cuadre_debito(movimientos, resumen, Decimal("5000"), Decimal("1500"))
        assert ok is True
        assert alertas == []

    def test_debito_descuadre_detecta_fila_faltante(self):
        """Prueba negativa: si falta un movimiento, el cuadre lo detecta."""
        from datetime import date
        movimientos = [
            Movimiento(
                fecha=date(2025, 12, 4), hora=None,
                descripcion="dep", identificador_transaccion="1",
                monto=Decimal("5000"), comision=Decimal("0"),
                moneda="MXN",
            ),
        ]
        resumen = _ResumenDebito(
            saldo_inicial=Decimal("1000"),
            depositos_declarados=Decimal("8300.50"),
            retiros_declarados=Decimal("4300.50"),
            saldo_final=Decimal("5000"),
        )
        ok, alertas = _validar_cuadre_debito(movimientos, resumen, Decimal("0"), Decimal("0"))
        assert ok is False
        assert len(alertas) > 0
        assert any("depositos" in a.lower() or "descuadre" in a.lower() for a in alertas)

    def test_credito_cuadra(self):
        from datetime import date
        movimientos = [
            Movimiento(
                fecha=date(2025, 11, 12), hora=None,
                descripcion="cargo", identificador_transaccion="1",
                monto=Decimal("200"), comision=Decimal("0"),
                moneda="MXN",
            ),
            Movimiento(
                fecha=date(2025, 11, 25), hora=None,
                descripcion="abono", identificador_transaccion="2",
                monto=Decimal("-100"), comision=Decimal("0"),
                moneda="MXN",
            ),
        ]
        ok, alertas = _validar_cuadre_credito(movimientos, Decimal("200"), Decimal("100"))
        assert ok is True

    def test_credito_descuadre(self):
        from datetime import date
        movimientos = [
            Movimiento(
                fecha=date(2025, 11, 12), hora=None,
                descripcion="cargo", identificador_transaccion="1",
                monto=Decimal("200"), comision=Decimal("0"),
                moneda="MXN",
            ),
        ]
        ok, alertas = _validar_cuadre_credito(movimientos, Decimal("500"), Decimal("0"))
        assert ok is False
        assert any("cargos" in a.lower() for a in alertas)


# ─── Utilidades ──────────────────────────────────────────────────────


class TestUtilidades:
    def test_parse_monto(self):
        assert _parse_monto("8,300.50") == Decimal("8300.50")
        assert _parse_monto("$ 1,000.00") == Decimal("1000.00")
        assert _parse_monto("0.00") == Decimal("0")
        assert _parse_monto("") == Decimal("0")

    def test_parse_fecha(self):
        from datetime import date
        assert _parse_fecha_ddmmmyyyy("04-DIC-2025") == date(2025, 12, 4)
        assert _parse_fecha_ddmmmyyyy("15-ENE-2026") == date(2026, 1, 15)

    def test_parse_fecha_invalida(self):
        with pytest.raises(ValueError):
            _parse_fecha_ddmmmyyyy("invalid")


# ─── Pipeline end-to-end via detector ────────────────────────────────


class TestPipelineDetector:
    def test_parsea_estado_de_cuenta_debito(self):
        e = parsea_estado_de_cuenta(DEBITO_RASTER)
        assert e.institucion == "Santander"
        assert len(e.movimientos) == 6
        assert e.es_confiable is True

    def test_parsea_estado_de_cuenta_credito(self):
        e = parsea_estado_de_cuenta(CREDITO_RASTER)
        assert e.institucion == "Santander"
        assert len(e.movimientos) == 6
        assert e.es_confiable is True


# ─── Prueba negativa deliberada (verificacion item 3) ───────────────


class TestValidacionAtrapaPSM6:
    """Simulates --psm 6 dropping a row: remove one movement line from
    real OCR output and prove the balance validation catches the shortfall.

    This is the deliberate negative test required by the prompt:
    'corre el parser forzando --psm 6 (o altera un fixture para eliminar
    una fila) y demuestra que la validacion de cuadre detecta el faltante
    y marca requiere_revision.'
    """

    def _ocr_sin_fila(self, path: Path, primer_monto_a_borrar: str = "5,000.00") -> list[str]:
        """OCR the real fixture, then drop the first movement line that
        contains the given amount — simulating psm 6 silent row loss."""
        paginas = ocr_paginas(path)
        resultado = []
        borrado = False
        for texto in paginas:
            lineas_nuevas = []
            for linea in texto.split("\n"):
                if not borrado and primer_monto_a_borrar in linea:
                    borrado = True
                    continue
                lineas_nuevas.append(linea)
            resultado.append("\n".join(lineas_nuevas))
        assert borrado, f"No se encontro linea con {primer_monto_a_borrar} para borrar"
        return resultado

    def test_debito_fila_borrada_descuadra(self):
        """Remove one deposit (2,300.50 — unique to movement table) — validation must fail."""
        paginas_alteradas = self._ocr_sin_fila(DEBITO_RASTER, "2,300.50")
        with patch("bank_parser.adapters.santander.ocr_paginas", return_value=paginas_alteradas):
            adapter = SantanderAdapter()
            extracto = adapter.parsea(DEBITO_RASTER)
        assert extracto.es_confiable is False
        assert len(extracto.alertas) > 0
        tiene_descuadre = any(
            "descuadre" in a.lower() or "depositos" in a.lower()
            for a in extracto.alertas
        )
        assert tiene_descuadre, f"Alertas no mencionan descuadre: {extracto.alertas}"
        assert len(extracto.movimientos) == 5

    def test_credito_fila_borrada_descuadra(self):
        """Remove one credit cargo — validation must fail."""
        paginas_alteradas = self._ocr_sin_fila(CREDITO_RASTER, "1,500.00")
        with patch("bank_parser.adapters.santander.ocr_paginas", return_value=paginas_alteradas):
            adapter = SantanderAdapter()
            extracto = adapter.parsea(CREDITO_RASTER)
        assert extracto.es_confiable is False
        assert len(extracto.alertas) > 0
        tiene_descuadre = any(
            "descuadre" in a.lower() or "cargos" in a.lower()
            for a in extracto.alertas
        )
        assert tiene_descuadre, f"Alertas no mencionan descuadre: {extracto.alertas}"
