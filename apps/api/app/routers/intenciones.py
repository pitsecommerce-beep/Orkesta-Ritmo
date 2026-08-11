from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase

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
async def registrar_intencion(
    intencion: IntencionPago,
    db: Client = Depends(get_supabase),
):
    if intencion.plan not in PLANES_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"Plan no válido. Opciones: {PLANES_VALIDOS}",
        )

    data = {"plan": intencion.plan}
    if intencion.email:
        data["email"] = intencion.email
    if intencion.tenant_id:
        data["tenant_id"] = intencion.tenant_id

    resp = db.table("intenciones_pago").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al registrar intención.")

    return {
        "status": "registered",
        "plan": intencion.plan,
        "message": "Tu interés ha sido registrado. Te avisaremos cuando el plan esté disponible.",
    }
