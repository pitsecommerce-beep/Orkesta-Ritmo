"""Excepciones del motor de calculo fiscal."""


class EjercicioNoDisponibleError(Exception):
    """El ejercicio fiscal solicitado no tiene tarifas cargadas.

    Debe traducirse a estado 'requiere_revision' en la capa API,
    nunca debe calcularse con tarifas vacias.
    """

    def __init__(self, year: int, motivo: str = "") -> None:
        self.year = year
        self.motivo = motivo
        msg = f"Ejercicio fiscal {year} no disponible"
        if motivo:
            msg += f": {motivo}"
        super().__init__(msg)


class RegimenEnValidacionError(Exception):
    """El regimen solicitado esta temporalmente deshabilitado.

    RESICO PM usa tarifas de PF que no son correctas para PM.
    Hasta que se implemente la tarifa correcta, el motor rechaza
    el calculo en lugar de producir resultados incorrectos.
    """

    def __init__(self, regimen: str, motivo: str = "") -> None:
        self.regimen = regimen
        self.motivo = motivo
        msg = f"Regimen {regimen} en validacion"
        if motivo:
            msg += f": {motivo}"
        super().__init__(msg)
