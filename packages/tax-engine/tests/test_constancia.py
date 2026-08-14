"""Tests para extracción de constancia de situación fiscal."""

import pytest

from tax_engine.constancia import (
    DatosConstancia,
    RegimenConstancia,
    derivar_regimen_de_constancia,
    extraer_constancia,
    mapear_regimen_sat,
)


class TestMapeoRegimenSat:
    """Traducción de claves SAT a regímenes del sistema."""

    def test_resico_pf(self):
        assert mapear_regimen_sat("612") == "RESICO_PF"

    def test_arrendamiento(self):
        assert mapear_regimen_sat("606") == "ARRENDAMIENTO"

    def test_regimen_no_soportado(self):
        assert mapear_regimen_sat("601") is None

    def test_resico_pm_no_soportado(self):
        """RESICO PM está deshabilitado (Block 1)."""
        assert mapear_regimen_sat("625") is None

    def test_clave_inexistente(self):
        assert mapear_regimen_sat("999") is None


class TestDerivarRegimen:
    """Derivación de régimen desde datos de constancia."""

    def test_un_solo_regimen_soportado(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="612", descripcion="RESICO", fecha_alta="2022-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "RESICO_PF"

    def test_arrendamiento_unico(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="606", descripcion="Arrendamiento", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "ARRENDAMIENTO"

    def test_multiples_regimenes_arrendamiento_prioridad(self):
        """Si tiene arrendamiento y RESICO PF, prevalece arrendamiento."""
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="612", descripcion="RESICO", fecha_alta="2022-01-01"),
                RegimenConstancia(clave_sat="606", descripcion="Arrendamiento", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "ARRENDAMIENTO"

    def test_ningun_regimen_soportado(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="601", descripcion="General", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) is None

    def test_sin_regimenes(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
        )
        assert derivar_regimen_de_constancia(datos) is None

    def test_regimen_no_vigente_ignorado(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="612", descripcion="RESICO", fecha_alta="2022-01-01", vigente=False),
            ],
        )
        assert derivar_regimen_de_constancia(datos) is None


class TestExtraerConstancia:
    """Extracción de datos del PDF de constancia."""

    def test_texto_vacio(self):
        datos = extraer_constancia("")
        assert not datos.valido
        assert "vacío" in datos.error

    def test_texto_solo_espacios(self):
        datos = extraer_constancia("   ")
        assert not datos.valido

    def test_pendiente_documento_real(self):
        """Sin documento real, la extracción devuelve error de pendiente."""
        datos = extraer_constancia("Texto de ejemplo que no es una constancia real")
        assert not datos.valido
        assert "pendiente" in datos.error.lower()
