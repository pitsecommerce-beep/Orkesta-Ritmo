from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

PLANES_VALIDOS = [
    "periodo_suelto",
    "esencial_mensual",
    "esencial_anual",
    "completo_mensual",
    "despacho",
]


class IntencionPago(BaseModel):
    plan: str
    email: Optional[str] = None
    tenant_id: Optional[str] = None


@router.post("/")
async def registrar_intencion(intencion: IntencionPago):
    return {
        "status": "registered",
        "plan": intencion.plan,
        "message": "Tu interés ha sido registrado. Te avisaremos cuando el plan esté disponible.",
    }
