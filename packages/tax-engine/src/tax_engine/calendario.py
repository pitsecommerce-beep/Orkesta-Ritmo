"""
Generación de calendario de obligaciones fiscales.

A partir del perfil del contribuyente y la tabla perfiles_obligacion,
genera los periodos de un ejercicio con sus fechas límite.

Reglas:
- ISR/IVA mensual: 12 periodos, vencimiento día 17 del mes siguiente.
- ISR/IVA trimestral: 4 periodos (ene-mar, abr-jun, jul-sep, oct-dic),
  vencimiento día 17 del mes siguiente al trimestre.
- ISR anual: 1 periodo, vencimiento en abril del año siguiente.
- Si la fecha límite cae en sábado, domingo o día inhábil bancario,
  se recorre al siguiente día hábil.
"""

import datetime
from dataclasses import dataclass


@dataclass
class PeriodoCalendario:
    """Un periodo de obligación fiscal generado."""
    impuesto: str  # "ISR" | "IVA"
    tipo_periodo: str  # "mensual" | "trimestral" | "anual"
    ejercicio: int
    numero_periodo: int  # 1-12 mensual, 1-4 trimestral, 0 anual
    fecha_limite: datetime.date
    es_pago_definitivo: bool = False


@dataclass
class ObligacionPerfil:
    """Configuración de obligación desde perfiles_obligacion."""
    impuesto: str
    tipo_periodo: str
    dia_limite: int
    admite_trimestral: bool
    presenta_anual: bool
    es_pago_definitivo: bool


DIAS_INHABILES_2025 = {
    datetime.date(2025, 1, 1),    # Año Nuevo
    datetime.date(2025, 2, 3),    # Constitución (primer lunes de febrero)
    datetime.date(2025, 3, 17),   # Natalicio Benito Juárez (tercer lunes de marzo)
    datetime.date(2025, 5, 1),    # Día del Trabajo
    datetime.date(2025, 9, 16),   # Independencia
    datetime.date(2025, 11, 17),  # Revolución (tercer lunes de noviembre)
    datetime.date(2025, 12, 25),  # Navidad
    # Semana Santa 2025: jueves y viernes santos
    datetime.date(2025, 4, 17),   # Jueves Santo
    datetime.date(2025, 4, 18),   # Viernes Santo
}

DIAS_INHABILES_2026 = {
    datetime.date(2026, 1, 1),    # Año Nuevo
    datetime.date(2026, 2, 2),    # Constitución
    datetime.date(2026, 3, 16),   # Natalicio Benito Juárez
    datetime.date(2026, 4, 2),    # Jueves Santo
    datetime.date(2026, 4, 3),    # Viernes Santo
    datetime.date(2026, 5, 1),    # Día del Trabajo
    datetime.date(2026, 9, 16),   # Independencia
    datetime.date(2026, 11, 16),  # Revolución
    datetime.date(2026, 12, 25),  # Navidad
}

_INHABILES: dict[int, set[datetime.date]] = {
    2025: DIAS_INHABILES_2025,
    2026: DIAS_INHABILES_2026,
}


def es_dia_habil(fecha: datetime.date) -> bool:
    """
    Determina si una fecha es día hábil bancario en México.

    No es hábil si es sábado, domingo o día inhábil oficial.
    """
    if fecha.weekday() >= 5:  # sábado=5, domingo=6
        return False

    inhabiles = _INHABILES.get(fecha.year, set())
    return fecha not in inhabiles


def siguiente_dia_habil(fecha: datetime.date) -> datetime.date:
    """
    Si la fecha no es hábil, avanza al siguiente día hábil.
    """
    while not es_dia_habil(fecha):
        fecha += datetime.timedelta(days=1)
    return fecha


def _fecha_limite_mensual(ejercicio: int, mes: int, dia: int) -> datetime.date:
    """
    Fecha límite para un periodo mensual: día `dia` del mes siguiente.
    Diciembre vence en enero del año siguiente.
    """
    if mes == 12:
        anio_vence = ejercicio + 1
        mes_vence = 1
    else:
        anio_vence = ejercicio
        mes_vence = mes + 1

    fecha = datetime.date(anio_vence, mes_vence, dia)
    return siguiente_dia_habil(fecha)


def _fecha_limite_trimestral(ejercicio: int, trimestre: int, dia: int) -> datetime.date:
    """
    Fecha límite para un periodo trimestral: día `dia` del mes siguiente
    al último mes del trimestre.
    Trimestre 1 (ene-mar) → abril, Trimestre 4 (oct-dic) → enero sig.
    """
    ultimo_mes = trimestre * 3
    if ultimo_mes == 12:
        anio_vence = ejercicio + 1
        mes_vence = 1
    else:
        anio_vence = ejercicio
        mes_vence = ultimo_mes + 1

    fecha = datetime.date(anio_vence, mes_vence, dia)
    return siguiente_dia_habil(fecha)


def _fecha_limite_anual(ejercicio: int) -> datetime.date:
    """
    Fecha límite para la declaración anual: abril del año siguiente.
    PF: último día hábil de abril (día 30 o anterior si inhábil).
    """
    fecha = datetime.date(ejercicio + 1, 4, 30)
    while not es_dia_habil(fecha):
        fecha -= datetime.timedelta(days=1)
    return fecha


def generar_calendario(
    ejercicio: int,
    obligaciones: list[ObligacionPerfil],
    opcion_trimestral: bool = False,
) -> list[PeriodoCalendario]:
    """
    Genera el calendario de periodos para un ejercicio.

    Args:
        ejercicio: Año fiscal (e.g. 2025).
        obligaciones: Lista de obligaciones del perfil (de perfiles_obligacion).
        opcion_trimestral: True si el contribuyente ejerce opción trimestral.

    Returns:
        Lista de PeriodoCalendario ordenada por fecha_limite.
    """
    periodos: list[PeriodoCalendario] = []

    for oblig in obligaciones:
        usa_trimestral = opcion_trimestral and oblig.admite_trimestral

        if usa_trimestral:
            for trim in range(1, 5):
                fecha = _fecha_limite_trimestral(ejercicio, trim, oblig.dia_limite)
                periodos.append(PeriodoCalendario(
                    impuesto=oblig.impuesto,
                    tipo_periodo="trimestral",
                    ejercicio=ejercicio,
                    numero_periodo=trim,
                    fecha_limite=fecha,
                    es_pago_definitivo=oblig.es_pago_definitivo,
                ))
        else:
            for mes in range(1, 13):
                fecha = _fecha_limite_mensual(ejercicio, mes, oblig.dia_limite)
                periodos.append(PeriodoCalendario(
                    impuesto=oblig.impuesto,
                    tipo_periodo="mensual",
                    ejercicio=ejercicio,
                    numero_periodo=mes,
                    fecha_limite=fecha,
                    es_pago_definitivo=oblig.es_pago_definitivo,
                ))

        if oblig.presenta_anual:
            fecha_anual = _fecha_limite_anual(ejercicio)
            periodos.append(PeriodoCalendario(
                impuesto=oblig.impuesto,
                tipo_periodo="anual",
                ejercicio=ejercicio,
                numero_periodo=0,
                fecha_limite=fecha_anual,
                es_pago_definitivo=False,
            ))

    periodos.sort(key=lambda p: (p.fecha_limite, p.impuesto))
    return periodos
