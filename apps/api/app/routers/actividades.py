from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()


class ActividadCreate(BaseModel):
    descripcion: str


class ActividadUpdate(BaseModel):
    descripcion: Optional[str] = None
    resultado: Optional[str] = None


@router.get("/")
async def list_actividades(
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("actividades")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"actividades": resp.data}


@router.post("/")
async def create_actividad(
    body: ActividadCreate,
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    data = {
        "tenant_id": tenant_id,
        "descripcion": body.descripcion,
    }
    resp = db.table("actividades").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al crear actividad.")
    return resp.data[0]


@router.patch("/{actividad_id}")
async def update_actividad(
    actividad_id: str,
    body: ActividadUpdate,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Nada que actualizar.")

    resp = db.table("actividades").update(updates).eq("id", actividad_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Actividad no encontrada.")
    return resp.data[0]


@router.get("/{actividad_id}/cobertura")
async def get_cobertura(
    actividad_id: str,
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    total_resp = (
        db.table("cfdis")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .eq("tipo", "I")
        .execute()
    )
    total_cfdis = total_resp.count or 0

    mapeados_resp = (
        db.table("cfdis")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .eq("tipo", "I")
        .not_.is_("actividad_id", "null")
        .execute()
    )
    mapeados = mapeados_resp.count or 0

    sin_mapear = total_cfdis - mapeados
    porcentaje = (mapeados / total_cfdis * 100) if total_cfdis > 0 else 0

    return {
        "total_cfdis": total_cfdis,
        "mapeados": mapeados,
        "sin_mapear": sin_mapear,
        "porcentaje": round(porcentaje, 1),
    }
