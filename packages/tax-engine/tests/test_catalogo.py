"""Tests para el catalogo normativo versionado.

Verifica resolucion por fecha, jerarquia, y coherencia de datos 2025/2026.
"""

import datetime
from decimal import Decimal

import pytest

from tax_engine.catalogo import (
    CatalogoNormativo,
    EstadoConfirmacion,
    Indicador,
    Jerarquia,
    ReglaFiscal,
    ReglaVersion,
    TipoIndicador,
    TipoTarifa,
)
from tax_engine.catalogo_data import obtener_catalogo
from tax_engine.exceptions import EjercicioNoDisponibleError


class TestUmaVigencia:
    """UMA cambia el 1 de febrero, no el 1 de enero."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_uma_enero_2025_usa_valor_2024(self):
        uma = self.cat.resolver_uma_diaria(datetime.date(2025, 1, 15))
        assert uma == Decimal("108.57")

    def test_uma_febrero_2025_usa_valor_2025(self):
        uma = self.cat.resolver_uma_diaria(datetime.date(2025, 2, 1))
        assert uma == Decimal("113.14")

    def test_uma_diciembre_2025_sigue_con_2025(self):
        uma = self.cat.resolver_uma_diaria(datetime.date(2025, 12, 31))
        assert uma == Decimal("113.14")

    def test_uma_enero_2026_sigue_con_2025(self):
        uma = self.cat.resolver_uma_diaria(datetime.date(2026, 1, 15))
        assert uma == Decimal("113.14")

    def test_uma_febrero_2026_usa_valor_2026(self):
        uma = self.cat.resolver_uma_diaria(datetime.date(2026, 2, 1))
        assert uma == Decimal("117.31")

    def test_uma_mensual_febrero_2026(self):
        mensual = self.cat.resolver_uma_mensual(datetime.date(2026, 3, 15))
        esperado = Decimal("117.31") * Decimal("30.4")
        assert mensual == esperado


class TestTarifaResolucion:
    """Resolucion de tarifas por tipo y fecha."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_art96_2025_tiene_11_tramos(self):
        tarifa = self.cat.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL,
            datetime.date(2025, 6, 15),
        )
        assert len(tarifa.tramos) == 11

    def test_art96_2026_tiene_11_tramos(self):
        tarifa = self.cat.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL,
            datetime.date(2026, 6, 15),
        )
        assert len(tarifa.tramos) == 11

    def test_art96_2026_limites_mayores_que_2025(self):
        t2025 = self.cat.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL,
            datetime.date(2025, 6, 15),
        )
        t2026 = self.cat.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL,
            datetime.date(2026, 6, 15),
        )
        for i in range(1, len(t2025.tramos)):
            assert t2026.tramos[i].limite_inferior > t2025.tramos[i].limite_inferior

    def test_resico_pf_2025_tiene_5_tramos(self):
        tarifa = self.cat.resolver_tarifa(
            TipoTarifa.RESICO_PF_MENSUAL,
            datetime.date(2025, 6, 15),
        )
        assert len(tarifa.tramos) == 5

    def test_resico_pf_iguales_2025_2026(self):
        t2025 = self.cat.resolver_tarifa(
            TipoTarifa.RESICO_PF_MENSUAL,
            datetime.date(2025, 6, 15),
        )
        t2026 = self.cat.resolver_tarifa(
            TipoTarifa.RESICO_PF_MENSUAL,
            datetime.date(2026, 6, 15),
        )
        for i in range(len(t2025.tramos)):
            assert t2025.tramos[i].tasa == t2026.tramos[i].tasa
            assert t2025.tramos[i].limite_superior == t2026.tramos[i].limite_superior

    def test_ultimo_tramo_art96_sin_limite_superior(self):
        tarifa = self.cat.resolver_tarifa(
            TipoTarifa.ART96_MENSUAL,
            datetime.date(2025, 6, 15),
        )
        assert tarifa.tramos[-1].limite_superior is None

    def test_fecha_sin_tarifa_lanza_error(self):
        with pytest.raises(EjercicioNoDisponibleError):
            self.cat.resolver_tarifa(
                TipoTarifa.ART96_MENSUAL,
                datetime.date(2020, 1, 1),
            )


class TestJerarquiaResolucion:
    """La regla de mayor jerarquia vigente gana."""

    def test_jerarquia_sustituye_gana_sobre_base(self):
        cat = CatalogoNormativo()
        cat.agregar_regla(ReglaFiscal(clave="TEST.REGLA", descripcion="test"))
        cat.agregar_version(ReglaVersion(
            id="v1", regla_clave="TEST.REGLA", valor=Decimal("10"),
            vigencia_desde=datetime.date(2025, 1, 1),
            jerarquia=Jerarquia.BASE,
        ))
        cat.agregar_version(ReglaVersion(
            id="v2", regla_clave="TEST.REGLA", valor=Decimal("20"),
            vigencia_desde=datetime.date(2025, 1, 1),
            jerarquia=Jerarquia.SUSTITUYE,
        ))
        resultado = cat.resolver_regla("TEST.REGLA", datetime.date(2025, 6, 1))
        assert resultado.valor == Decimal("20")

    def test_version_fuera_de_vigencia_ignorada(self):
        cat = CatalogoNormativo()
        cat.agregar_regla(ReglaFiscal(clave="TEST.REGLA", descripcion="test"))
        cat.agregar_version(ReglaVersion(
            id="v1", regla_clave="TEST.REGLA", valor=Decimal("10"),
            vigencia_desde=datetime.date(2025, 1, 1),
            vigencia_hasta=datetime.date(2025, 6, 1),
            jerarquia=Jerarquia.BASE,
        ))
        cat.agregar_version(ReglaVersion(
            id="v2", regla_clave="TEST.REGLA", valor=Decimal("20"),
            vigencia_desde=datetime.date(2025, 6, 1),
            jerarquia=Jerarquia.BASE,
        ))
        resultado = cat.resolver_regla("TEST.REGLA", datetime.date(2025, 7, 1))
        assert resultado.valor == Decimal("20")

    def test_sin_version_vigente_lanza_error(self):
        cat = CatalogoNormativo()
        cat.agregar_regla(ReglaFiscal(clave="TEST.REGLA", descripcion="test"))
        with pytest.raises(EjercicioNoDisponibleError):
            cat.resolver_regla("TEST.REGLA", datetime.date(2025, 1, 1))


class TestPlataformasLif2026:
    """LIF 2026 Art. 25 fr. VI sustituye tasa LISR Art. 113-A para enajenacion."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_enajenacion_2025_tasa_base(self):
        regla = self.cat.resolver_regla(
            "PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS",
            datetime.date(2025, 6, 15),
        )
        assert regla.valor == Decimal("1")
        assert regla.jerarquia == Jerarquia.BASE

    def test_enajenacion_2026_tasa_lif_sustituye(self):
        regla = self.cat.resolver_regla(
            "PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS",
            datetime.date(2026, 6, 15),
        )
        assert regla.valor == Decimal("2.5")
        assert regla.jerarquia == Jerarquia.SUSTITUYE


class TestPendientesContador:
    """Reglas marcadas PENDIENTE_CONTADOR deben existir con ese estado."""

    def setup_method(self):
        self.cat = obtener_catalogo()

    def test_existen_reglas_pendiente_contador(self):
        pendientes = [
            v for v in self.cat.versiones
            if v.estado == EstadoConfirmacion.PENDIENTE_CONTADOR
        ]
        assert len(pendientes) >= 1

    def test_pendientes_tienen_nota(self):
        pendientes = [
            v for v in self.cat.versiones
            if v.estado == EstadoConfirmacion.PENDIENTE_CONTADOR
        ]
        for p in pendientes:
            assert p.nota_confirmacion != ""


class TestResicoPf2026VsEneroMarzo:
    """RESICO PF para enero 2026 usa UMA de 2025; marzo 2026 usa UMA de 2026."""

    def test_uma_enero_2026_es_la_de_2025(self):
        cat = obtener_catalogo()
        uma_enero = cat.resolver_uma_mensual(datetime.date(2026, 1, 15))
        uma_esperada = Decimal("113.14") * Decimal("30.4")
        assert uma_enero == uma_esperada

    def test_uma_marzo_2026_es_la_de_2026(self):
        cat = obtener_catalogo()
        uma_marzo = cat.resolver_uma_mensual(datetime.date(2026, 3, 15))
        uma_esperada = Decimal("117.31") * Decimal("30.4")
        assert uma_marzo == uma_esperada

    def test_umas_distintas_enero_vs_marzo(self):
        cat = obtener_catalogo()
        uma_enero = cat.resolver_uma_mensual(datetime.date(2026, 1, 15))
        uma_marzo = cat.resolver_uma_mensual(datetime.date(2026, 3, 15))
        assert uma_marzo > uma_enero


class TestDecimalEverywhere:
    """Ningun valor numerico en el catalogo debe ser float."""

    def test_indicadores_son_decimal(self):
        cat = obtener_catalogo()
        for ind in cat.indicadores:
            assert isinstance(ind.valor, Decimal), f"Indicador {ind.id} tiene float"

    def test_tarifas_tramos_son_decimal(self):
        cat = obtener_catalogo()
        for tarifa in cat.tarifas:
            for tramo in tarifa.tramos:
                assert isinstance(tramo.limite_inferior, Decimal)
                assert isinstance(tramo.cuota_fija, Decimal)
                assert isinstance(tramo.porcentaje, Decimal)
                if tramo.limite_superior is not None:
                    assert isinstance(tramo.limite_superior, Decimal)
                if tramo.tasa is not None:
                    assert isinstance(tramo.tasa, Decimal)

    def test_regla_versiones_son_decimal(self):
        cat = obtener_catalogo()
        for v in cat.versiones:
            assert isinstance(v.valor, Decimal), f"Version {v.id} tiene float"
