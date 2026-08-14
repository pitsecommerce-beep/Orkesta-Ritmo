"""
Validación de RFC (Registro Federal de Contribuyentes).

Reglas:
- Persona física: 13 caracteres (4 letras + 6 dígitos fecha + 3 homoclave)
- Persona moral: 12 caracteres (3 letras + 6 dígitos fecha + 3 homoclave)
- Letras admitidas: A-Z, Ñ, & (& solo para personas morales)
- Los 6 dígitos centrales representan AAMMDD (año, mes, día)
- La homoclave es alfanumérica
"""

import re
from dataclasses import dataclass


_RE_PF = re.compile(
    r"^[A-ZÑ&]{4}"
    r"(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"
    r"[A-Z0-9]{3}$"
)

_RE_PM = re.compile(
    r"^[A-ZÑ&]{3}"
    r"(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"
    r"[A-Z0-9]{3}$"
)


@dataclass
class ResultadoRfc:
    valido: bool
    rfc: str
    tipo_persona: str  # "fisica" | "moral" | ""
    error: str = ""


def validar_rfc(rfc_raw: str) -> ResultadoRfc:
    """
    Valida un RFC mexicano y determina si es persona física o moral.

    Reglas:
    - Limpia espacios y convierte a mayúsculas.
    - 13 caracteres → persona física (4 letras iniciales).
    - 12 caracteres → persona moral (3 letras iniciales).
    - Los 6 dígitos centrales deben ser una fecha AAMMDD válida.
    - La homoclave (últimos 3) debe ser alfanumérica.

    Returns:
        ResultadoRfc con el resultado de la validación.
    """
    rfc = rfc_raw.strip().upper()

    if not rfc:
        return ResultadoRfc(valido=False, rfc=rfc, tipo_persona="", error="RFC vacío")

    if len(rfc) == 13:
        if not _RE_PF.match(rfc):
            return ResultadoRfc(
                valido=False,
                rfc=rfc,
                tipo_persona="fisica",
                error="Formato inválido para persona física (esperado: 4 letras + AAMMDD + 3 alfanuméricos)",
            )
        return ResultadoRfc(valido=True, rfc=rfc, tipo_persona="fisica")

    if len(rfc) == 12:
        if not _RE_PM.match(rfc):
            return ResultadoRfc(
                valido=False,
                rfc=rfc,
                tipo_persona="moral",
                error="Formato inválido para persona moral (esperado: 3 letras + AAMMDD + 3 alfanuméricos)",
            )
        return ResultadoRfc(valido=True, rfc=rfc, tipo_persona="moral")

    return ResultadoRfc(
        valido=False,
        rfc=rfc,
        tipo_persona="",
        error=f"RFC debe tener 12 (moral) o 13 (física) caracteres, tiene {len(rfc)}",
    )
