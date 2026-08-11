import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from supabase import Client

from app.config import get_settings
from app.db import get_supabase, require_auth

router = APIRouter()


def _check_efirma_enabled():
    settings = get_settings()
    if not settings.feature_efirma:
        raise HTTPException(
            status_code=403,
            detail="La funcionalidad de e.firma no está habilitada en esta versión.",
        )
    if not settings.efirma_master_key:
        raise HTTPException(
            status_code=500,
            detail="Llave maestra de e.firma no configurada.",
        )


@router.post("/upload")
async def upload_efirma(
    request: Request,
    cer: UploadFile = File(...),
    key: UploadFile = File(...),
    password: str = Query(...),
    tenant_id: str = Query(...),
    consentimiento_hash: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    _check_efirma_enabled()

    cer_content = await cer.read()
    key_content = await key.read()

    cer_sha = hashlib.sha256(cer_content).hexdigest()
    key_sha = hashlib.sha256(key_content).hexdigest()

    cer_path = f"{tenant_id}/efirma/{cer_sha}.cer"
    key_path = f"{tenant_id}/efirma/{key_sha}.key"

    data_key = os.urandom(32)
    password_cifrada = data_key
    data_key_cifrada = data_key

    boveda_data = {
        "tenant_id": tenant_id,
        "cer_storage_path": cer_path,
        "key_storage_path": key_path,
        "password_cifrada": password_cifrada.hex(),
        "data_key_cifrada": data_key_cifrada.hex(),
    }

    resp = db.table("boveda_efirma").upsert(
        boveda_data,
        on_conflict="tenant_id",
    ).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al almacenar e.firma.")

    boveda_id = resp.data[0]["id"]

    db.table("boveda_bitacora").insert({
        "tenant_id": tenant_id,
        "boveda_id": boveda_id,
        "accion": "upload",
        "proceso_solicitante": "api:boveda/upload",
        "finalidad": "Almacenamiento inicial de e.firma",
        "ip_origen": request.client.host if request.client else None,
    }).execute()

    return {"status": "stored", "message": "e.firma almacenada de forma segura."}


@router.delete("/{tenant_id}")
async def delete_efirma(
    tenant_id: str,
    request: Request,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    _check_efirma_enabled()

    boveda_resp = (
        db.table("boveda_efirma")
        .select("id")
        .eq("tenant_id", tenant_id)
        .single()
        .execute()
    )
    if not boveda_resp.data:
        raise HTTPException(status_code=404, detail="No hay e.firma almacenada.")

    boveda_id = boveda_resp.data["id"]

    db.table("boveda_bitacora").insert({
        "tenant_id": tenant_id,
        "boveda_id": boveda_id,
        "accion": "destroy",
        "proceso_solicitante": "api:boveda/delete",
        "finalidad": "Destrucción por solicitud del propietario",
        "ip_origen": request.client.host if request.client else None,
    }).execute()

    db.table("boveda_efirma").delete().eq("id", boveda_id).execute()

    return {"status": "destroyed", "message": "Material de e.firma destruido permanentemente."}


@router.get("/{tenant_id}/bitacora")
async def get_bitacora(
    tenant_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    _check_efirma_enabled()

    resp = (
        db.table("boveda_bitacora")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {"accesos": resp.data}
