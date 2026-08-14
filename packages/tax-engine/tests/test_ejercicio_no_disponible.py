"""Tests para EjercicioNoDisponibleError.

Un ejercicio sin tarifas debe lanzar error, no calcular cero.
"""

from decimal import Decimal

import pytest

from tax_engine.engine import calcular
from tax_engine.exceptions import EjercicioNoDisponibleError, RegimenEnValidacionError
from tax_engine.types import PerfilFiscal, Regimen
from tests.conftest import make_cfdi_pue


class TestEjercicioNoDisponible:
    """Ejercicios sin tarifas lanzan EjercicioNoDisponibleError."""

    def test_year_sin_datos_lanza_error(self):
        cfdi = make_cfdi_pue(uuid="test-nd-01", subtotal=Decimal("10000"))
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        with pytest.raises(EjercicioNoDisponibleError) as exc_info:
            calcular([cfdi], perfil, ejercicio_year=2030, periodo=1)

        assert exc_info.value.year == 2030
        assert "2030" in str(exc_info.value)

    def test_2026_resico_tarifas_vacias_lanza_error(self):
        cfdi = make_cfdi_pue(uuid="test-nd-02", subtotal=Decimal("10000"))
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")

        with pytest.raises(EjercicioNoDisponibleError) as exc_info:
            calcular([cfdi], perfil, ejercicio_year=2026, periodo=1)

        assert exc_info.value.year == 2026
        assert "RESICO" in exc_info.value.motivo

    def test_2026_arrendamiento_tarifas_vacias_lanza_error(self):
        cfdi = make_cfdi_pue(uuid="test-nd-03", subtotal=Decimal("10000"))
        perfil = PerfilFiscal(regimen=Regimen.ARRENDAMIENTO, rfc="XAXX010101000")

        with pytest.raises(EjercicioNoDisponibleError) as exc_info:
            calcular([cfdi], perfil, ejercicio_year=2026, periodo=1)

        assert exc_info.value.year == 2026
        assert "Art. 96" in exc_info.value.motivo

    def test_resico_pm_lanza_regimen_en_validacion(self):
        """RESICO PM lanza RegimenEnValidacionError antes de verificar tarifas."""
        cfdi = make_cfdi_pue(uuid="test-nd-04", subtotal=Decimal("10000"))
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PM, rfc="XAX010101000")

        with pytest.raises(RegimenEnValidacionError) as exc_info:
            calcular([cfdi], perfil, ejercicio_year=2025, periodo=1)

        assert exc_info.value.regimen == "RESICO_PM"

    def test_es_subclase_de_exception(self):
        err = EjercicioNoDisponibleError(2026, "sin tarifas")
        assert isinstance(err, Exception)
        assert not isinstance(err, ValueError)


class TestEjercicio2025SigueFuncionando:
    """2025 con tarifas cargadas debe calcular normalmente."""

    def test_resico_pf_2025_calcula(self):
        cfdi = make_cfdi_pue(uuid="test-ok-01", subtotal=Decimal("20000"))
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PF, rfc="XAXX010101000")
        resultado = calcular([cfdi], perfil, ejercicio_year=2025, periodo=1)

        assert resultado.isr.ingresos == Decimal("20000")
        assert resultado.isr.isr_a_cargo > Decimal("0")

    def test_arrendamiento_2025_calcula(self):
        cfdi = make_cfdi_pue(uuid="test-ok-02", subtotal=Decimal("30000"))
        perfil = PerfilFiscal(regimen=Regimen.ARRENDAMIENTO, rfc="XAXX010101000")
        resultado = calcular([cfdi], perfil, ejercicio_year=2025, periodo=1)

        assert resultado.isr.ingresos == Decimal("30000")
        assert resultado.isr.isr_a_cargo >= Decimal("0")
