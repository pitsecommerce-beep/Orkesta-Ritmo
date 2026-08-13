from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()


class PeriodoResponse(BaseModel):
    id: str
    impuesto: str
    tipo_periodo: str
    ejercicio: int
    numero_periodo: int
    fecha_limite: str
    estado: str


@router.get("/")
async def list_periodos(
    tenant_id: str = Query(...),
    ejercicio: Optional[int] = None,
    impuesto: Optional[str] = None,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    query = db.table("periodos").select("*").eq("tenant_id", tenant_id)
    if ejercicio is not None:
        query = query.eq("ejercicio", ejercicio)
    if impuesto is not None:
        query = query.eq("impuesto", impuesto)
    query = query.order("ejercicio", desc=True).order("numero_periodo", desc=True)
    resp = query.execute()
    return {"periodos": resp.data}


@router.get("/{periodo_id}")
async def get_periodo(
    periodo_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("periodos").select("*").eq("id", periodo_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")
    return resp.data


@router.get("/{periodo_id}/desglose")
async def get_desglose(
    periodo_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("periodos").select("*").eq("id", periodo_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")

    periodo = resp.data
    resultado = periodo.get("resultado_json") or {}
    return {
        "periodo_id": periodo_id,
        "estado": periodo["estado"],
        "isr": resultado.get("isr"),
        "iva": resultado.get("iva"),
        "trazabilidad": resultado.get("trazabilidad", []),
        "alertas": resultado.get("alertas", []),
    }


@router.post("/{periodo_id}/marcar-presentado")
async def marcar_presentado(
    periodo_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    profile_resp = (
        db.table("user_profiles")
        .select("email_verificado")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not profile_resp.data or not profile_resp.data.get("email_verificado"):
        raise HTTPException(
            status_code=403,
            detail="Debes verificar tu correo electronico para presentar la declaracion.",
        )

    current = db.table("periodos").select("estado, tenant_id").eq("id", periodo_id).single().execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")

    estado_actual = current.data["estado"]
    estados_validos = ("calculado", "contrastado", "preparado")
    if estado_actual not in estados_validos:
        raise HTTPException(
            status_code=422,
            detail=f"No se puede marcar como presentado desde estado '{estado_actual}'.",
        )

    resp = db.table("periodos").update({"estado": "presentado"}).eq("id", periodo_id).execute()

    db.table("bitacora_periodos").insert({
        "tenant_id": current.data["tenant_id"],
        "periodo_id": periodo_id,
        "estado_anterior": estado_actual,
        "estado_nuevo": "presentado",
    }).execute()

    return resp.data[0] if resp.data else {"id": periodo_id, "estado": "presentado"}
