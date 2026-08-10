"""Tests enfocados en el algoritmo de deteccion de pares espejo.

Los movimientos espejo son pares internos de Mercado Pago con el mismo
ID de transaccion y montos exactamente opuestos. Representan movimientos
internos y NO deben contarse como ingreso ni como gasto.

Sin esta deteccion, el ingreso se sobreestima hasta un 68%.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bank_parser.adapters.mercado_pago import MercadoPagoAdapter
from bank_parser.types import ExtractoBancario, Movimiento, NivelConfianza


def _crea_extracto_con_movimientos(
    movimientos: list[Movimiento],
) -> ExtractoBancario:
    """Crea un ExtractoBancario minimo para testing de espejos."""
    return ExtractoBancario(
        institucion="Mercado Pago",
        titular="T***",
        identificador_cuenta="****1234",
        periodo_inicio=date(2025, 10, 1),
        periodo_fin=date(2025, 10, 31),
        saldo_inicial=Decimal("0"),
        saldo_final=Decimal("0"),
        total_abonos_declarado=Decimal("0"),
        total_cargos_declarado=Decimal("0"),
        comisiones_declaradas=Decimal("0"),
        movimientos=movimientos,
    )


def _crea_movimiento(
    id_tx: str, monto: Decimal, descripcion: str = "Transferencia recibida"
) -> Movimiento:
    """Crea un Movimiento minimo para testing."""
    return Movimiento(
        fecha=date(2025, 10, 1),
        hora=None,
        descripcion=descripcion,
        identificador_transaccion=id_tx,
        monto=monto,
        comision=Decimal("0"),
        moneda="MXN",
    )


class TestParesEspejoBasico:
    """Tests basicos de deteccion de pares espejo."""

    def test_par_perfecto_detectado(self) -> None:
        """Dos movimientos con mismo ID y montos opuestos = espejo."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 1
        assert extracto.movimientos[0].es_espejo is True
        assert extracto.movimientos[1].es_espejo is True

    def test_movimiento_sin_par_no_marcado(self) -> None:
        """Un movimiento solo no debe marcarse como espejo."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1002", Decimal("-300.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 0
        assert extracto.movimientos[0].es_espejo is False
        assert extracto.movimientos[1].es_espejo is False

    def test_mismo_id_pero_montos_no_opuestos(self) -> None:
        """Mismo ID pero montos que no suman cero: no es espejo."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-300.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 0
        assert extracto.movimientos[0].es_espejo is False
        assert extracto.movimientos[1].es_espejo is False


class TestIdTransaccionCero:
    """Tests para el caso especial de ID de transaccion '0'."""

    def test_id_cero_no_se_empareja(self) -> None:
        """Movimientos con ID '0' NO deben emparejarse entre si.

        El ID '0' es generico en Mercado Pago y no identifica
        una transaccion especifica.
        """
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("0", Decimal("100.00")),
            _crea_movimiento("0", Decimal("-100.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 0
        assert extracto.movimientos[0].es_espejo is False
        assert extracto.movimientos[1].es_espejo is False

    def test_id_cero_mezclado_con_pares_reales(self) -> None:
        """Los ID '0' no deben interferir con pares reales."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("0", Decimal("100.00")),
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
            _crea_movimiento("0", Decimal("-100.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 1
        assert extracto.movimientos[0].es_espejo is False  # ID "0"
        assert extracto.movimientos[1].es_espejo is True   # Par real
        assert extracto.movimientos[2].es_espejo is True   # Par real
        assert extracto.movimientos[3].es_espejo is False  # ID "0"


class TestMultiplesPares:
    """Tests con multiples pares espejo."""

    def test_multiples_pares_distintos_ids(self) -> None:
        """Varios pares con distintos IDs se detectan todos."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1002", Decimal("300.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
            _crea_movimiento("1002", Decimal("-300.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 2
        assert all(m.es_espejo for m in extracto.movimientos)

    def test_tres_movimientos_mismo_id_solo_un_par(self) -> None:
        """Con 3 movimientos del mismo ID, solo 1 par se forma."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
            _crea_movimiento("1001", Decimal("500.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 1
        # El tercer movimiento no tiene par
        espejos = [m for m in extracto.movimientos if m.es_espejo]
        assert len(espejos) == 2

    def test_cuatro_movimientos_mismo_id_dos_pares(self) -> None:
        """Con 4 movimientos (2 positivos, 2 negativos), se forman 2 pares."""
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
            _crea_movimiento("1001", Decimal("500.00")),
            _crea_movimiento("1001", Decimal("-500.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert len(extracto.pares_espejo) == 2
        assert all(m.es_espejo for m in extracto.movimientos)


class TestNetosConEspejos:
    """Tests de calculo de montos netos excluyendo espejos."""

    def test_abono_neto_excluye_espejos(self) -> None:
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("1000.00")),
            _crea_movimiento("1001", Decimal("-1000.00")),
            _crea_movimiento("1002", Decimal("500.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert extracto.abono_neto == Decimal("500.00")

    def test_cargo_neto_excluye_espejos(self) -> None:
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("1000.00")),
            _crea_movimiento("1001", Decimal("-1000.00")),
            _crea_movimiento("1002", Decimal("-200.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert extracto.cargo_neto == Decimal("-200.00")

    def test_alerta_espejo_incluye_total(self) -> None:
        adapter = MercadoPagoAdapter()
        movs = [
            _crea_movimiento("1001", Decimal("750.00")),
            _crea_movimiento("1001", Decimal("-750.00")),
        ]
        extracto = _crea_extracto_con_movimientos(movs)
        adapter._detecta_espejos(extracto)

        assert any("750" in a for a in extracto.alertas)
