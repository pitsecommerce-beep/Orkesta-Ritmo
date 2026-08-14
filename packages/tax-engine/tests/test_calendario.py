"""Tests para generación de calendario de obligaciones fiscales."""

import datetime

import pytest

from tax_engine.calendario import (
    ObligacionPerfil,
    PeriodoCalendario,
    es_dia_habil,
    generar_calendario,
    siguiente_dia_habil,
)


# --- Fixtures de obligaciones por régimen ---

def _obligaciones_resico_pf():
    return [
        ObligacionPerfil(
            impuesto="ISR", tipo_periodo="mensual", dia_limite=17,
            admite_trimestral=False, presenta_anual=False, es_pago_definitivo=True,
        ),
        ObligacionPerfil(
            impuesto="IVA", tipo_periodo="mensual", dia_limite=17,
            admite_trimestral=False, presenta_anual=False, es_pago_definitivo=False,
        ),
    ]


def _obligaciones_arrendamiento():
    return [
        ObligacionPerfil(
            impuesto="ISR", tipo_periodo="mensual", dia_limite=17,
            admite_trimestral=True, presenta_anual=True, es_pago_definitivo=False,
        ),
        ObligacionPerfil(
            impuesto="IVA", tipo_periodo="mensual", dia_limite=17,
            admite_trimestral=True, presenta_anual=False, es_pago_definitivo=False,
        ),
    ]


class TestDiasHabiles:
    """Validación de días hábiles bancarios."""

    def test_lunes_normal_es_habil(self):
        assert es_dia_habil(datetime.date(2025, 1, 6))

    def test_sabado_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 1, 4))

    def test_domingo_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 1, 5))

    def test_anio_nuevo_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 1, 1))

    def test_dia_trabajo_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 5, 1))

    def test_navidad_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 12, 25))

    def test_jueves_santo_2025_no_es_habil(self):
        assert not es_dia_habil(datetime.date(2025, 4, 17))

    def test_anio_sin_datos_asume_habil(self):
        """Un año sin datos de inhábiles asume que no hay feriados."""
        assert es_dia_habil(datetime.date(2030, 1, 1))  # miércoles


class TestSiguienteDiaHabil:
    """Avance al siguiente día hábil."""

    def test_dia_habil_no_cambia(self):
        lunes = datetime.date(2025, 1, 6)
        assert siguiente_dia_habil(lunes) == lunes

    def test_sabado_avanza_a_lunes(self):
        sabado = datetime.date(2025, 1, 4)
        assert siguiente_dia_habil(sabado) == datetime.date(2025, 1, 6)

    def test_domingo_avanza_a_lunes(self):
        domingo = datetime.date(2025, 1, 5)
        assert siguiente_dia_habil(domingo) == datetime.date(2025, 1, 6)

    def test_feriado_viernes_avanza_a_lunes(self):
        """Viernes Santo 2025 (18 abr) → lunes 21 abr."""
        viernes_santo = datetime.date(2025, 4, 18)
        assert siguiente_dia_habil(viernes_santo) == datetime.date(2025, 4, 21)

    def test_jueves_santo_avanza_pasando_viernes_a_lunes(self):
        """Jueves Santo 2025 (17 abr) → lunes 21 abr (viernes 18 también inhábil)."""
        jueves_santo = datetime.date(2025, 4, 17)
        assert siguiente_dia_habil(jueves_santo) == datetime.date(2025, 4, 21)


class TestCalendarioResicoPf:
    """Calendario para RESICO PF: 12 ISR + 12 IVA = 24 periodos."""

    def test_total_periodos(self):
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        assert len(periodos) == 24

    def test_sin_periodo_anual(self):
        """RESICO PF no presenta anual."""
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        anuales = [p for p in periodos if p.tipo_periodo == "anual"]
        assert len(anuales) == 0

    def test_primer_periodo_isr_enero(self):
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        isr_enero = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 1]
        assert len(isr_enero) == 1
        assert isr_enero[0].fecha_limite == datetime.date(2025, 2, 17)

    def test_diciembre_vence_en_enero_siguiente(self):
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        isr_dic = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 12]
        assert len(isr_dic) == 1
        assert isr_dic[0].fecha_limite.year == 2026
        assert isr_dic[0].fecha_limite.month == 1

    def test_es_pago_definitivo_isr(self):
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        isr = [p for p in periodos if p.impuesto == "ISR"]
        assert all(p.es_pago_definitivo for p in isr)

    def test_iva_no_es_definitivo(self):
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        iva = [p for p in periodos if p.impuesto == "IVA"]
        assert all(not p.es_pago_definitivo for p in iva)

    def test_opcion_trimestral_sin_efecto(self):
        """RESICO PF no admite trimestral, la opción se ignora."""
        periodos = generar_calendario(2025, _obligaciones_resico_pf(), opcion_trimestral=True)
        assert len(periodos) == 24
        assert all(p.tipo_periodo == "mensual" for p in periodos)


class TestCalendarioArrendamiento:
    """Calendario para Arrendamiento."""

    def test_mensual_total_periodos(self):
        """Sin trimestral: 12 ISR + 12 IVA + 1 anual ISR = 25."""
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        assert len(periodos) == 25

    def test_incluye_anual_isr(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        anuales = [p for p in periodos if p.tipo_periodo == "anual"]
        assert len(anuales) == 1
        assert anuales[0].impuesto == "ISR"

    def test_anual_vence_en_abril(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        anual = [p for p in periodos if p.tipo_periodo == "anual"][0]
        assert anual.fecha_limite.month == 4
        assert anual.fecha_limite.year == 2026

    def test_anual_ultimo_dia_habil_abril(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        anual = [p for p in periodos if p.tipo_periodo == "anual"][0]
        assert es_dia_habil(anual.fecha_limite)
        assert anual.fecha_limite.month == 4

    def test_trimestral_total_periodos(self):
        """Con trimestral: 4 ISR + 4 IVA + 1 anual ISR = 9."""
        periodos = generar_calendario(2025, _obligaciones_arrendamiento(), opcion_trimestral=True)
        assert len(periodos) == 9

    def test_trimestral_periodos_correctos(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento(), opcion_trimestral=True)
        isr_trim = [p for p in periodos if p.impuesto == "ISR" and p.tipo_periodo == "trimestral"]
        assert len(isr_trim) == 4
        assert [p.numero_periodo for p in isr_trim] == [1, 2, 3, 4]

    def test_trimestre1_vence_en_abril(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento(), opcion_trimestral=True)
        t1 = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 1 and p.tipo_periodo == "trimestral"]
        assert len(t1) == 1
        assert t1[0].fecha_limite.month == 4
        assert t1[0].fecha_limite.day == 17 or t1[0].fecha_limite.day > 17

    def test_trimestre4_vence_en_enero_siguiente(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento(), opcion_trimestral=True)
        t4 = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 4 and p.tipo_periodo == "trimestral"]
        assert len(t4) == 1
        assert t4[0].fecha_limite.year == 2026
        assert t4[0].fecha_limite.month == 1


class TestDiaLimiteConFeriados:
    """Fechas límite que caen en feriado o fin de semana se recorren."""

    def test_mayo_17_2025_es_sabado(self):
        """17 mayo 2025 es sábado, se recorre a lunes 19."""
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        isr_abril = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 4]
        assert isr_abril[0].fecha_limite == datetime.date(2025, 5, 19)

    def test_agosto_17_2025_es_domingo(self):
        """17 agosto 2025 es domingo, se recorre a lunes 18."""
        periodos = generar_calendario(2025, _obligaciones_resico_pf())
        isr_julio = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 7]
        assert isr_julio[0].fecha_limite == datetime.date(2025, 8, 18)

    def test_semana_santa_2025_trimestral(self):
        """17 abril 2025 es Jueves Santo; trimestre 1 vence lunes 21."""
        periodos = generar_calendario(2025, _obligaciones_arrendamiento(), opcion_trimestral=True)
        t1_isr = [p for p in periodos if p.impuesto == "ISR" and p.numero_periodo == 1 and p.tipo_periodo == "trimestral"]
        assert t1_isr[0].fecha_limite == datetime.date(2025, 4, 21)

    def test_todas_las_fechas_son_habiles(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        for p in periodos:
            assert es_dia_habil(p.fecha_limite), (
                f"{p.impuesto} periodo {p.numero_periodo}: "
                f"{p.fecha_limite} no es día hábil"
            )

    def test_orden_por_fecha(self):
        periodos = generar_calendario(2025, _obligaciones_arrendamiento())
        fechas = [p.fecha_limite for p in periodos]
        assert fechas == sorted(fechas)
