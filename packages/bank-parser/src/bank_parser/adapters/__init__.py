"""Adaptadores de estados de cuenta para distintas instituciones bancarias."""

from bank_parser.adapters.bbva import BBVAAdapter
from bank_parser.adapters.mercado_pago import MercadoPagoAdapter
from bank_parser.adapters.nu import NuAdapter
from bank_parser.adapters.revolut import RevolutAdapter
from bank_parser.adapters.santander import SantanderAdapter

TODOS_LOS_ADAPTADORES = [
    MercadoPagoAdapter(),
    SantanderAdapter(),
    BBVAAdapter(),
    NuAdapter(),
    RevolutAdapter(),
]

__all__ = [
    "BBVAAdapter",
    "MercadoPagoAdapter",
    "NuAdapter",
    "RevolutAdapter",
    "SantanderAdapter",
    "TODOS_LOS_ADAPTADORES",
]
