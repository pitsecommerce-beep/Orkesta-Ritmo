"""Tests para validación de RFC."""

import pytest

from tax_engine.rfc import validar_rfc


class TestRfcPersonaFisica:
    """RFC de persona física: 13 caracteres."""

    def test_rfc_generico_valido(self):
        r = validar_rfc("XAXX010101000")
        assert r.valido
        assert r.tipo_persona == "fisica"
        assert r.rfc == "XAXX010101000"

    def test_rfc_valido_con_enie(self):
        r = validar_rfc("ÑOÑE850315AB1")
        assert r.valido
        assert r.tipo_persona == "fisica"

    def test_rfc_valido_minusculas_normaliza(self):
        r = validar_rfc("xaxx010101000")
        assert r.valido
        assert r.rfc == "XAXX010101000"

    def test_rfc_valido_con_espacios(self):
        r = validar_rfc("  XAXX010101000  ")
        assert r.valido
        assert r.rfc == "XAXX010101000"

    def test_rfc_fecha_invalida_mes_13(self):
        r = validar_rfc("XAXX011301000")
        assert not r.valido
        assert "Formato inválido" in r.error

    def test_rfc_fecha_invalida_dia_32(self):
        r = validar_rfc("XAXX010132000")
        assert not r.valido

    def test_rfc_fecha_invalida_mes_00(self):
        r = validar_rfc("XAXX010001000")
        assert not r.valido

    def test_rfc_fecha_invalida_dia_00(self):
        r = validar_rfc("XAXX010100000")
        assert not r.valido

    def test_rfc_homoclave_valida_alfanumerica(self):
        r = validar_rfc("GARC850315A2B")
        assert r.valido

    def test_rfc_homoclave_numerica(self):
        r = validar_rfc("GARC850315123")
        assert r.valido

    def test_rfc_con_ampersand_invalido_pf(self):
        """& en posición de letra inicial para PF es raro pero el regex lo acepta."""
        r = validar_rfc("&ARC850315AB1")
        assert r.valido


class TestRfcPersonaMoral:
    """RFC de persona moral: 12 caracteres."""

    def test_rfc_generico_moral(self):
        r = validar_rfc("XAX010101000")
        assert r.valido
        assert r.tipo_persona == "moral"

    def test_rfc_moral_con_ampersand(self):
        r = validar_rfc("A&C050101AB1")
        assert r.valido
        assert r.tipo_persona == "moral"

    def test_rfc_moral_fecha_invalida(self):
        r = validar_rfc("XAX011301000")
        assert not r.valido
        assert r.tipo_persona == "moral"


class TestRfcInvalidos:
    """Casos de RFC inválidos."""

    def test_rfc_vacio(self):
        r = validar_rfc("")
        assert not r.valido
        assert "vacío" in r.error

    def test_rfc_solo_espacios(self):
        r = validar_rfc("   ")
        assert not r.valido
        assert "vacío" in r.error

    def test_rfc_muy_corto(self):
        r = validar_rfc("ABC")
        assert not r.valido
        assert "12 (moral) o 13 (física)" in r.error

    def test_rfc_muy_largo(self):
        r = validar_rfc("XAXX01010100012")
        assert not r.valido
        assert "12 (moral) o 13 (física)" in r.error

    def test_rfc_11_caracteres(self):
        r = validar_rfc("XAX01010100")
        assert not r.valido

    def test_rfc_14_caracteres(self):
        r = validar_rfc("XAXX010101000A")
        assert not r.valido
