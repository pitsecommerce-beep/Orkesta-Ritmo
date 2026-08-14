"""
Tests para RESICO Persona Moral — deshabilitado.

RESICO PM esta temporalmente deshabilitado porque usaba tarifas
de PF que no son correctas para PM. El engine debe rechazar
el calculo con RegimenEnValidacionError.
"""

from decimal import Decimal

import pytest

from tax_engine.engine import calcular
from tax_engine.exceptions import RegimenEnValidacionError
from tax_engine.types import PerfilFiscal, Regimen
from tests.conftest import make_cfdi_pue


class TestResicoPmDeshabilitado:
    """RESICO PM debe lanzar RegimenEnValidacionError."""

    def test_engine_rechaza_resico_pm(self):
        cfdi = make_cfdi_pue(uuid="pm-disabled-01", subtotal=Decimal("20000"))
        perfil = PerfilFiscal(regimen=Regimen.RESICO_PM, rfc="XAX010101000")

        with pytest.raises(RegimenEnValidacionError) as exc_info:
            calcular(
                cfdis_emitidos=[cfdi],
                perfil=perfil,
                ejercicio_year=2025,
                periodo=1,
            )

        assert exc_info.value.regimen == "RESICO_PM"
        assert "tarifa" in str(exc_info.value).lower() or "validacion" in str(exc_info.value).lower()

    def test_error_es_subclase_de_exception(self):
        err = RegimenEnValidacionError("RESICO_PM", "test")
        assert isinstance(err, Exception)
        assert not isinstance(err, ValueError)
