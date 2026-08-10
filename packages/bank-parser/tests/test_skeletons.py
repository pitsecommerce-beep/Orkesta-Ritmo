"""Tests para los adaptadores skeleton (pendientes de implementacion).

Todos los tests en este modulo estan marcados como skip porque
los adaptadores aun no estan implementados.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bank_parser.adapters.bbva import BBVAAdapter
from bank_parser.adapters.nu import NuAdapter
from bank_parser.adapters.revolut import RevolutAdapter
from bank_parser.adapters.santander import SantanderAdapter
from bank_parser.base import BankAdapter


@pytest.mark.skip(reason="Adapter pending implementation")
class TestSantander:
    def test_parsea(self) -> None:
        adapter = SantanderAdapter()
        adapter.parsea(Path("dummy.pdf"))

    def test_detecta(self) -> None:
        adapter = SantanderAdapter()
        assert adapter.detecta("Santander estado de cuenta") is True


@pytest.mark.skip(reason="Adapter pending implementation")
class TestBBVA:
    def test_parsea(self) -> None:
        adapter = BBVAAdapter()
        adapter.parsea(Path("dummy.pdf"))

    def test_detecta(self) -> None:
        adapter = BBVAAdapter()
        assert adapter.detecta("BBVA estado de cuenta") is True


@pytest.mark.skip(reason="Adapter pending implementation")
class TestNu:
    def test_parsea(self) -> None:
        adapter = NuAdapter()
        adapter.parsea(Path("dummy.pdf"))

    def test_detecta(self) -> None:
        adapter = NuAdapter()
        assert adapter.detecta("Nu estado de cuenta") is True


@pytest.mark.skip(reason="Adapter pending implementation")
class TestRevolut:
    def test_parsea(self) -> None:
        adapter = RevolutAdapter()
        adapter.parsea(Path("dummy.pdf"))

    def test_detecta(self) -> None:
        adapter = RevolutAdapter()
        assert adapter.detecta("Revolut statement") is True


class TestSkeletonsRaiseNotImplemented:
    """Verifica que los skeletons lanzan NotImplementedError."""

    def test_santander_not_implemented(self) -> None:
        adapter = SantanderAdapter()
        with pytest.raises(NotImplementedError, match="Santander"):
            adapter.parsea(Path("dummy.pdf"))

    def test_bbva_not_implemented(self) -> None:
        adapter = BBVAAdapter()
        with pytest.raises(NotImplementedError, match="BBVA"):
            adapter.parsea(Path("dummy.pdf"))

    def test_nu_not_implemented(self) -> None:
        adapter = NuAdapter()
        with pytest.raises(NotImplementedError, match="Nu"):
            adapter.parsea(Path("dummy.pdf"))

    def test_revolut_not_implemented(self) -> None:
        adapter = RevolutAdapter()
        with pytest.raises(NotImplementedError, match="Revolut"):
            adapter.parsea(Path("dummy.pdf"))


class TestSkeletonsDetectaReturnFalse:
    """Verifica que los skeletons no detectan nada."""

    def test_santander_detecta_false(self) -> None:
        assert SantanderAdapter().detecta("cualquier texto") is False

    def test_bbva_detecta_false(self) -> None:
        assert BBVAAdapter().detecta("cualquier texto") is False

    def test_nu_detecta_false(self) -> None:
        assert NuAdapter().detecta("cualquier texto") is False

    def test_revolut_detecta_false(self) -> None:
        assert RevolutAdapter().detecta("cualquier texto") is False


class TestSkeletonsConformanProtocolo:
    """Verifica que los skeletons cumplen el protocolo BankAdapter."""

    def test_santander_is_bank_adapter(self) -> None:
        assert isinstance(SantanderAdapter(), BankAdapter)

    def test_bbva_is_bank_adapter(self) -> None:
        assert isinstance(BBVAAdapter(), BankAdapter)

    def test_nu_is_bank_adapter(self) -> None:
        assert isinstance(NuAdapter(), BankAdapter)

    def test_revolut_is_bank_adapter(self) -> None:
        assert isinstance(RevolutAdapter(), BankAdapter)

    def test_mercado_pago_is_bank_adapter(self) -> None:
        from bank_parser.adapters.mercado_pago import MercadoPagoAdapter

        assert isinstance(MercadoPagoAdapter(), BankAdapter)
