from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


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
async def list_tenants():
    return {"tenants": []}


@router.post("/")
async def create_tenant(tenant: TenantCreate):
    if len(tenant.rfc) == 13:
        tipo_persona = "fisica"
    elif len(tenant.rfc) == 12:
        tipo_persona = "moral"
    else:
        raise HTTPException(status_code=400, detail="RFC debe tener 12 o 13 caracteres")

    admitidos = ["RESICO_PF", "RESICO_PF_SUELDOS", "ARRENDAMIENTO", "ARRENDAMIENTO_SUELDOS", "RESICO_PM"]
    if tenant.regimen not in admitidos:
        raise HTTPException(
            status_code=422,
            detail=f"El régimen {tenant.regimen} no está soportado en esta versión. Tu registro se guardó en la lista de espera.",
        )

    return {"id": "placeholder", "rfc": tenant.rfc, "tipo_persona": tipo_persona}


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str):
    return {"id": tenant_id}


@router.patch("/{tenant_id}")
async def update_tenant(tenant_id: str, update: TenantUpdate):
    return {"id": tenant_id, "updated": True}


@router.post("/{tenant_id}/invite")
async def invite_member(tenant_id: str, invite: InviteMember):
    valid_roles = ["contador", "lectura"]
    if invite.rol not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Rol debe ser uno de: {valid_roles}")
    return {"status": "invited", "email": invite.email, "rol": invite.rol}


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    return {"status": "deleted"}
