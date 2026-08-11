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
