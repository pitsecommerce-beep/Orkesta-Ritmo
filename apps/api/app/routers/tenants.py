from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()

REGIMENES_ADMITIDOS = [
    "RESICO_PF", "RESICO_PF_SUELDOS",
    "ARRENDAMIENTO", "ARRENDAMIENTO_SUELDOS",
]


class TenantCreate(BaseModel):
    rfc: str
    nombre: str
    regimen: str
    tipo_deduccion: str = "ciega"
    opcion_trimestral: bool = False


class TenantUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_deduccion: Optional[str] = None
    opcion_trimestral: Optional[bool] = None
    presenta_anual: Optional[bool] = None


class InviteMember(BaseModel):
    email: str
    rol: str = "lectura"


@router.get("/")
async def list_tenants(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("tenants").select("*").execute()
    return {"tenants": resp.data}


@router.post("/")
async def create_tenant(
    body: TenantCreate,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if body.regimen not in REGIMENES_ADMITIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"Regimen '{body.regimen}' no soportado. Admitidos: {REGIMENES_ADMITIDOS}",
        )

    rfc_limpio = body.rfc.strip().upper()
    if len(rfc_limpio) == 12:
        tipo_persona = "moral"
    elif len(rfc_limpio) == 13:
        tipo_persona = "fisica"
    else:
        raise HTTPException(status_code=422, detail="RFC debe tener 12 o 13 caracteres.")

    tenant_data = {
        "rfc": rfc_limpio,
        "nombre": body.nombre,
        "tipo_persona": tipo_persona,
        "regimen": body.regimen,
        "tipo_deduccion": body.tipo_deduccion,
        "opcion_trimestral": body.opcion_trimestral,
    }
    resp = db.table("tenants").insert(tenant_data).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al crear contribuyente.")

    tenant = resp.data[0]

    db.table("memberships").insert({
        "tenant_id": tenant["id"],
        "user_id": user_id,
        "rol": "propietario",
    }).execute()

    return tenant


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("tenants").select("*").eq("id", tenant_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Contribuyente no encontrado.")
    return resp.data


@router.patch("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Nada que actualizar.")

    resp = db.table("tenants").update(updates).eq("id", tenant_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Contribuyente no encontrado.")
    return resp.data[0]


@router.post("/{tenant_id}/invite")
async def invite_member(
    tenant_id: str,
    body: InviteMember,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if body.rol not in ("contador", "lectura"):
        raise HTTPException(status_code=422, detail="Rol debe ser 'contador' o 'lectura'.")

    return {
        "status": "invited",
        "tenant_id": tenant_id,
        "email": body.email,
        "rol": body.rol,
    }


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("tenants").delete().eq("id", tenant_id).execute()
    return {"status": "deleted", "tenant_id": tenant_id}
