"""
Tarifas fiscales hardcoded — fallback para tests.

En producción la fuente de verdad es la tabla `ejercicios` + `tarifas_resico`
+ `tarifas_art96` en Supabase.  Este archivo existe para que los tests del
motor puedan ejecutarse sin conexión a base de datos.
"""

from decimal import Decimal
from typing import Optional

from tax_engine.types import Ejercicio, TramoArt96, TramoResico


def _tarifas_resico_2025() -> list[TramoResico]:
    """Tarifa RESICO mensual para el ejercicio 2025."""
    return [
        TramoResico(
            limite_superior=Decimal("25000.00"),
            tasa=Decimal("1.00"),
        ),
        TramoResico(
            limite_superior=Decimal("50000.00"),
            tasa=Decimal("1.10"),
        ),
        TramoResico(
            limite_superior=Decimal("83888.33"),
            tasa=Decimal("1.50"),
        ),
        TramoResico(
            limite_superior=Decimal("208333.33"),
            tasa=Decimal("2.00"),
        ),
        TramoResico(
            limite_superior=Decimal("291666.66"),
            tasa=Decimal("2.50"),
        ),
    ]


def _tarifas_art96_2025() -> list[TramoArt96]:
    """Tarifa Art. 96 LISR mensual para el ejercicio 2025."""
    return [
        TramoArt96(
            limite_inferior=Decimal("0.01"),
            limite_superior=Decimal("844.59"),
            cuota_fija=Decimal("0.00"),
            porcentaje=Decimal("1.92"),
        ),
        TramoArt96(
            limite_inferior=Decimal("844.60"),
            limite_superior=Decimal("7168.51"),
            cuota_fija=Decimal("16.22"),
            porcentaje=Decimal("6.40"),
        ),
        TramoArt96(
            limite_inferior=Decimal("7168.52"),
            limite_superior=Decimal("12598.02"),
            cuota_fija=Decimal("420.95"),
            porcentaje=Decimal("10.88"),
        ),
        TramoArt96(
            limite_inferior=Decimal("12598.03"),
            limite_superior=Decimal("14644.64"),
            cuota_fija=Decimal("1011.68"),
            porcentaje=Decimal("16.00"),
        ),
        TramoArt96(
            limite_inferior=Decimal("14644.65"),
            limite_superior=Decimal("17533.64"),
            cuota_fija=Decimal("1339.14"),
            porcentaje=Decimal("17.92"),
        ),
        TramoArt96(
            limite_inferior=Decimal("17533.65"),
            limite_superior=Decimal("35362.83"),
            cuota_fija=Decimal("1856.84"),
            porcentaje=Decimal("21.36"),
        ),
        TramoArt96(
            limite_inferior=Decimal("35362.84"),
            limite_superior=Decimal("55736.68"),
            cuota_fija=Decimal("5665.16"),
            porcentaje=Decimal("23.52"),
        ),
        TramoArt96(
            limite_inferior=Decimal("55736.69"),
            limite_superior=Decimal("106410.50"),
            cuota_fija=Decimal("10457.09"),
            porcentaje=Decimal("30.00"),
        ),
        TramoArt96(
            limite_inferior=Decimal("106410.51"),
            limite_superior=Decimal("141880.66"),
            cuota_fija=Decimal("25659.23"),
            porcentaje=Decimal("32.00"),
        ),
        TramoArt96(
            limite_inferior=Decimal("141880.67"),
            limite_superior=Decimal("425641.99"),
            cuota_fija=Decimal("37009.69"),
            porcentaje=Decimal("34.00"),
        ),
        TramoArt96(
            limite_inferior=Decimal("425642.00"),
            limite_superior=None,
            cuota_fija=Decimal("133488.54"),
            porcentaje=Decimal("35.00"),
        ),
    ]


def obtener_ejercicio(year: int) -> Optional[Ejercicio]:
    """
    Obtiene los datos del ejercicio fiscal para el year dado.

    Args:
        year: Year del ejercicio fiscal.

    Returns:
        Ejercicio con tarifas y parametros, o None si no esta disponible.
    """
    if year == 2025:
        return Ejercicio(
            year=2025,
            umas_mensuales=Decimal("3300.53"),
            tarifas_resico=_tarifas_resico_2025(),
            tarifas_art96=_tarifas_art96_2025(),
        )
    elif year == 2026:
        # Ejercicio 2026: tarifas aun no publicadas
        return Ejercicio(
            year=2026,
            umas_mensuales=Decimal("0"),
            tarifas_resico=[],
            tarifas_art96=[],
        )
    return None


def buscar_tramo_resico(
    ingreso_mensual: Decimal,
    tarifas: list[TramoResico],
) -> Optional[TramoResico]:
    """
    Busca el tramo aplicable en la tarifa RESICO por ingreso mensual.

    Args:
        ingreso_mensual: Ingreso mensual total.
        tarifas: Lista de tramos RESICO ordenados por limite superior.

    Returns:
        TramoResico aplicable, o None si el ingreso excede todos los tramos.
    """
    for tramo in tarifas:
        if ingreso_mensual <= tramo.limite_superior:
            return tramo
    return None


def buscar_tramo_art96(
    base_gravable: Decimal,
    tarifas: list[TramoArt96],
) -> Optional[TramoArt96]:
    """
    Busca el tramo aplicable en la tarifa del Art. 96 por base gravable.

    Args:
        base_gravable: Base gravable despues de deducciones.
        tarifas: Lista de tramos Art. 96 ordenados por limite inferior.

    Returns:
        TramoArt96 aplicable, o None si la base es menor a 0.01.
    """
    if base_gravable < Decimal("0.01"):
        return None
    for tramo in tarifas:
        if tramo.limite_superior is None or base_gravable <= tramo.limite_superior:
            if base_gravable >= tramo.limite_inferior:
                return tramo
    return None
