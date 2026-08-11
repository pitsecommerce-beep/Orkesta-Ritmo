from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()


@router.get("/")
async def list_cfdis(
    tenant_id: str = Query(...),
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    sin_actividad: Optional[bool] = None,
    periodo_id: Optional[str] = None,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    query = db.table("cfdis").select("*").eq("tenant_id", tenant_id)
    if tipo:
        query = query.eq("tipo", tipo)
    if estado:
        query = query.eq("estado", estado)
    if sin_actividad:
        query = query.is_("actividad_id", "null")
    if periodo_id:
        query = query.eq("periodo_id", periodo_id)
    query = query.order("fecha_emision", desc=True)
    resp = query.execute()
    return {"cfdis": resp.data}


@router.get("/ppd-pendientes")
async def ppd_pendientes(
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("cfdis")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("metodo_pago", "PPD")
        .eq("estado", "pendiente_complemento")
        .order("fecha_emision", desc=True)
        .execute()
    )
    return {"ppd_pendientes": resp.data}


@router.get("/{cfdi_id}")
async def get_cfdi(
    cfdi_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("cfdis").select("*").eq("id", cfdi_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="CFDI no encontrado.")
    return resp.data


@router.post("/{cfdi_id}/asignar-actividad")
async def asignar_actividad(
    cfdi_id: str,
    actividad_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("cfdis")
        .update({"actividad_id": actividad_id})
        .eq("id", cfdi_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="CFDI no encontrado.")
    return {"cfdi_id": cfdi_id, "actividad_id": actividad_id, "status": "assigned"}
