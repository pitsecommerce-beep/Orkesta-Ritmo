"""Tests completos para el adaptador de Mercado Pago.

Cubre los hallazgos verificados de estados de cuenta reales:
1. Validacion de totales (no formula de saldo)
2. Deteccion de movimientos espejo
3. Contradiccion de comisiones
4. Clasificacion de retenciones
5. Extraccion de detalles SPEI
6. Alertas por descripciones desconocidas
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest

from bank_parser.adapters.mercado_pago import (
    DESCRIPCIONES_CONOCIDAS,
    MercadoPagoAdapter,
    parsea_texto_mercado_pago,
)
from bank_parser.types import ExtractoBancario, NivelConfianza


@pytest.fixture
def extracto(mercado_pago_sample_text: str) -> ExtractoBancario:
    """Extracto parseado del fixture de Mercado Pago."""
    return parsea_texto_mercado_pago(mercado_pago_sample_text)


@pytest.fixture
def adapter() -> MercadoPagoAdapter:
    return MercadoPagoAdapter()


# -----------------------------------------------------------------------
# 1. Parseo del encabezado
# -----------------------------------------------------------------------
class TestEncabezado:
    """Tests de parseo del encabezado del estado de cuenta."""

    def test_total_abonos_declarado(self, extracto: ExtractoBancario) -> None:
        assert extracto.total_abonos_declarado == Decimal("23365.25")

    def test_total_cargos_declarado(self, extracto: ExtractoBancario) -> None:
        assert extracto.total_cargos_declarado == Decimal("26248.49")

    def test_saldo_inicial(self, extracto: ExtractoBancario) -> None:
        assert extracto.saldo_inicial == Decimal("0.00")

    def test_saldo_final(self, extracto: ExtractoBancario) -> None:
        assert extracto.saldo_final == Decimal("0.00")

    def test_comisiones_declaradas(self, extracto: ExtractoBancario) -> None:
        assert extracto.comisiones_declaradas == Decimal("0.00")

    def test_periodo(self, extracto: ExtractoBancario) -> None:
        assert extracto.periodo_inicio == date(2025, 10, 1)
        assert extracto.periodo_fin == date(2025, 10, 31)

    def test_titular_enmascarado(self, extracto: ExtractoBancario) -> None:
        # El nombre debe estar enmascarado
        assert "MARIA" not in extracto.titular
        assert "HERNANDEZ" not in extracto.titular
        assert "***" in extracto.titular

    def test_cuenta_enmascarada(self, extracto: ExtractoBancario) -> None:
        # La cuenta/CVU debe estar enmascarada con ultimos 4 digitos visibles
        assert extracto.identificador_cuenta.endswith("4567")
        assert "*" in extracto.identificador_cuenta

    def test_institucion(self, extracto: ExtractoBancario) -> None:
        assert extracto.institucion == "Mercado Pago"


# -----------------------------------------------------------------------
# 2. Parseo de movimientos
# -----------------------------------------------------------------------
class TestMovimientos:
    """Tests de parseo de movimientos individuales."""

    def test_cantidad_total_movimientos(
        self, extracto: ExtractoBancario
    ) -> None:
        assert len(extracto.movimientos) == 26

    def test_primer_movimiento_fecha(
        self, extracto: ExtractoBancario
    ) -> None:
        mov = extracto.movimientos[0]
        assert mov.fecha == date(2025, 10, 1)

    def test_primer_movimiento_hora(self, extracto: ExtractoBancario) -> None:
        mov = extracto.movimientos[0]
        assert mov.hora == time(8, 15, 30)

    def test_primer_movimiento_descripcion(
        self, extracto: ExtractoBancario
    ) -> None:
        mov = extracto.movimientos[0]
        assert mov.descripcion == "Transferencia recibida"

    def test_primer_movimiento_id(self, extracto: ExtractoBancario) -> None:
        mov = extracto.movimientos[0]
        assert mov.identificador_transaccion == "80001001"

    def test_primer_movimiento_monto_positivo(
        self, extracto: ExtractoBancario
    ) -> None:
        # Abono = positivo
        mov = extracto.movimientos[0]
        assert mov.monto == Decimal("1500.00")
        assert mov.monto > 0

    def test_cargo_monto_negativo(self, extracto: ExtractoBancario) -> None:
        # Segundo movimiento es cargo = negativo
        mov = extracto.movimientos[1]
        assert mov.monto == Decimal("-800.00")
        assert mov.monto < 0

    def test_moneda(self, extracto: ExtractoBancario) -> None:
        assert all(m.moneda == "MXN" for m in extracto.movimientos)

    def test_comision_parseada(self, extracto: ExtractoBancario) -> None:
        # Segundo movimiento tiene comision de 35.00
        mov = extracto.movimientos[1]
        assert mov.comision == Decimal("-35.00")

    def test_id_transaccion_cero(self, extracto: ExtractoBancario) -> None:
        """Los IDs '0' deben parsearse correctamente."""
        movs_cero = [
            m
            for m in extracto.movimientos
            if m.identificador_transaccion == "0"
        ]
        assert len(movs_cero) == 2


# -----------------------------------------------------------------------
# 3. Deteccion de movimientos espejo
# -----------------------------------------------------------------------
class TestEspejos:
    """Tests de deteccion de pares espejo."""

    def test_cantidad_pares_espejo(self, extracto: ExtractoBancario) -> None:
        assert len(extracto.pares_espejo) == 4

    def test_movimientos_marcados_como_espejo(
        self, extracto: ExtractoBancario
    ) -> None:
        espejos = [m for m in extracto.movimientos if m.es_espejo]
        assert len(espejos) == 8  # 4 pares = 8 movimientos

    def test_montos_espejo_opuestos(self, extracto: ExtractoBancario) -> None:
        """Cada par espejo debe tener montos que sumen exactamente cero."""
        for idx_a, idx_b in extracto.pares_espejo:
            mov_a = extracto.movimientos[idx_a]
            mov_b = extracto.movimientos[idx_b]
            assert mov_a.monto + mov_b.monto == Decimal("0")

    def test_ids_espejo_coinciden(self, extracto: ExtractoBancario) -> None:
        """Cada par espejo debe tener el mismo ID de transaccion."""
        for idx_a, idx_b in extracto.pares_espejo:
            mov_a = extracto.movimientos[idx_a]
            mov_b = extracto.movimientos[idx_b]
            assert (
                mov_a.identificador_transaccion
                == mov_b.identificador_transaccion
            )

    def test_alerta_espejos_generada(
        self, extracto: ExtractoBancario
    ) -> None:
        alertas_espejo = [
            a for a in extracto.alertas if "espejo" in a.lower()
        ]
        assert len(alertas_espejo) >= 1


# -----------------------------------------------------------------------
# 4. Montos netos (excluyendo espejos)
# -----------------------------------------------------------------------
class TestMontosNetos:
    """Tests de calculo de montos netos excluyendo espejos."""

    def test_abono_neto(self, extracto: ExtractoBancario) -> None:
        # Total abonos 23365.25 - espejos abono 5480.00 = 17885.25
        assert extracto.abono_neto == Decimal("17885.25")

    def test_cargo_neto(self, extracto: ExtractoBancario) -> None:
        # Total cargos 26248.49 - espejos cargo 5480.00 = 20768.49
        assert extracto.cargo_neto == Decimal("-20768.49")

    def test_abono_neto_menor_que_bruto(
        self, extracto: ExtractoBancario
    ) -> None:
        """Sin deteccion de espejos el ingreso se sobreestimaria."""
        assert extracto.abono_neto < extracto.total_abonos_declarado


# -----------------------------------------------------------------------
# 5. Validacion de comisiones
# -----------------------------------------------------------------------
class TestComisiones:
    """Tests de validacion de comisiones."""

    def test_contradiccion_comisiones_detectada(
        self, extracto: ExtractoBancario
    ) -> None:
        alertas_comision = [
            a for a in extracto.alertas if "comision" in a.lower()
        ]
        assert len(alertas_comision) >= 1

    def test_movimientos_con_comision_marcados_no_confiable(
        self, extracto: ExtractoBancario
    ) -> None:
        """Movimientos con comision deben marcarse como NO_CONFIABLE."""
        for mov in extracto.movimientos:
            if mov.comision != Decimal("0"):
                assert mov.confianza == NivelConfianza.NO_CONFIABLE


# -----------------------------------------------------------------------
# 6. Clasificacion de movimientos especiales
# -----------------------------------------------------------------------
class TestClasificacion:
    """Tests de clasificacion de movimientos."""

    def test_dinero_retenido_clasificado(
        self, extracto: ExtractoBancario
    ) -> None:
        retenciones = [
            m
            for m in extracto.movimientos
            if m.categoria == "retencion_temporal"
        ]
        assert len(retenciones) >= 1

    def test_dinero_retenido_es_cargo(
        self, extracto: ExtractoBancario
    ) -> None:
        retenciones = [
            m
            for m in extracto.movimientos
            if m.categoria == "retencion_temporal"
        ]
        for m in retenciones:
            assert m.monto < 0


# -----------------------------------------------------------------------
# 7. Extraccion de detalles SPEI
# -----------------------------------------------------------------------
class TestSPEI:
    """Tests de extraccion de informacion SPEI."""

    def test_clave_rastreo_extraida(
        self, extracto: ExtractoBancario
    ) -> None:
        mov = extracto.movimientos[0]
        assert "clave_rastreo" in mov.detalle
        assert mov.detalle["clave_rastreo"] == "MPE2025100100001"

    def test_clabe_enmascarada(self, extracto: ExtractoBancario) -> None:
        mov = extracto.movimientos[0]
        assert "clabe" in mov.detalle
        # CLABE debe estar enmascarada
        assert "*" in mov.detalle["clabe"]
        assert mov.detalle["clabe"].endswith("4567")

    def test_beneficiario_enmascarado(
        self, extracto: ExtractoBancario
    ) -> None:
        mov = extracto.movimientos[0]
        assert "beneficiario" in mov.detalle
        assert "***" in mov.detalle["beneficiario"]
        assert "MARIA" not in mov.detalle["beneficiario"]


# -----------------------------------------------------------------------
# 8. Alertas por descripciones desconocidas
# -----------------------------------------------------------------------
class TestDescripciones:
    """Tests de verificacion de descripciones."""

    def test_sin_alertas_descripciones_conocidas(
        self, extracto: ExtractoBancario
    ) -> None:
        """El fixture solo tiene descripciones conocidas."""
        alertas_desc = [
            a
            for a in extracto.alertas
            if "descripcion no reconocida" in a.lower()
        ]
        assert len(alertas_desc) == 0

    def test_descripcion_desconocida_genera_alerta(self) -> None:
        """Una descripcion no reconocida debe generar alerta."""
        texto = """Mercado Pago - Estado de Cuenta
Titular: JUAN PEREZ
CVU: 1234567890123456
Periodo: 01/10/2025 al 31/10/2025

Saldo inicial: $0.00
Saldo final: $100.00
Total de abonos: $100.00
Total de cargos: $0.00
Comisiones: $0.00

Movimientos

01/10/2025 10:00:00 Abono - Movimiento misterioso 99999 100.00 0.00 MXN
"""
        extracto = parsea_texto_mercado_pago(texto)
        alertas_desc = [
            a
            for a in extracto.alertas
            if "descripcion no reconocida" in a.lower()
        ]
        assert len(alertas_desc) == 1
        assert "Movimiento misterioso" in alertas_desc[0]


# -----------------------------------------------------------------------
# 9. Validacion contra totales declarados
# -----------------------------------------------------------------------
class TestValidacionTotales:
    """Tests de validacion de sumas contra encabezado."""

    def test_totales_coinciden_fixture_es_confiable(
        self, extracto: ExtractoBancario
    ) -> None:
        """Con el fixture correcto, los totales coinciden."""
        assert extracto.es_confiable is True

    def test_discrepancia_marca_no_confiable(self) -> None:
        """Si los movimientos no suman lo declarado, es no_confiable."""
        texto = """Mercado Pago - Estado de Cuenta
Titular: JUAN PEREZ
CVU: 1234567890123456
Periodo: 01/10/2025 al 31/10/2025

Saldo inicial: $0.00
Saldo final: $0.00
Total de abonos: $5,000.00
Total de cargos: $5,000.00
Comisiones: $0.00

Movimientos

01/10/2025 10:00:00 Abono - Transferencia recibida 10001 1,000.00 0.00 MXN
01/10/2025 11:00:00 Cargo - Transferencia enviada 10002 1,000.00 0.00 MXN
"""
        extracto = parsea_texto_mercado_pago(texto)
        assert extracto.es_confiable is False
        alertas_total = [
            a for a in extracto.alertas if "no coincide" in a.lower()
        ]
        assert len(alertas_total) >= 1


# -----------------------------------------------------------------------
# 10. Deteccion de institucion
# -----------------------------------------------------------------------
class TestDeteccion:
    """Tests de deteccion de la institucion."""

    def test_detecta_mercado_pago(self, adapter: MercadoPagoAdapter) -> None:
        texto = "Mercado Pago - Estado de Cuenta\nSaldo inicial: $0.00"
        assert adapter.detecta(texto) is True

    def test_no_detecta_otro_banco(
        self, adapter: MercadoPagoAdapter
    ) -> None:
        texto = "BBVA Bancomer - Estado de Cuenta\nSaldo inicial: $0.00"
        assert adapter.detecta(texto) is False

    def test_detecta_mercadopago_junto(
        self, adapter: MercadoPagoAdapter
    ) -> None:
        texto = "MercadoPago\nEstado de cuenta\nTotal de abonos: $100.00"
        assert adapter.detecta(texto) is True


# -----------------------------------------------------------------------
# Uso de Decimal (nunca float)
# -----------------------------------------------------------------------
class TestDecimal:
    """Verifica que todos los montos sean Decimal, nunca float."""

    def test_montos_son_decimal(self, extracto: ExtractoBancario) -> None:
        for mov in extracto.movimientos:
            assert isinstance(mov.monto, Decimal), (
                f"monto de {mov.descripcion} es {type(mov.monto)}, "
                f"debe ser Decimal"
            )
            assert isinstance(mov.comision, Decimal), (
                f"comision de {mov.descripcion} es {type(mov.comision)}, "
                f"debe ser Decimal"
            )

    def test_totales_son_decimal(self, extracto: ExtractoBancario) -> None:
        assert isinstance(extracto.saldo_inicial, Decimal)
        assert isinstance(extracto.saldo_final, Decimal)
        assert isinstance(extracto.total_abonos_declarado, Decimal)
        assert isinstance(extracto.total_cargos_declarado, Decimal)
        assert isinstance(extracto.abono_neto, Decimal)
        assert isinstance(extracto.cargo_neto, Decimal)
