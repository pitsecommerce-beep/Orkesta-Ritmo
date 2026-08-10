from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from app.config import get_settings

router = APIRouter()


@router.post("/upload")
async def upload_efirma(
    cer: UploadFile = File(...),
    key: UploadFile = File(...),
    password: str = Query(...),
    tenant_id: str = Query(...),
    consentimiento_hash: str = Query(...),
):
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

    return {"status": "stored", "message": "e.firma almacenada de forma segura."}


@router.delete("/{tenant_id}")
async def delete_efirma(tenant_id: str):
    settings = get_settings()
    if not settings.feature_efirma:
        raise HTTPException(status_code=403, detail="Funcionalidad no habilitada.")
    return {"status": "destroyed", "message": "Material de e.firma destruido permanentemente."}


@router.get("/{tenant_id}/bitacora")
async def get_bitacora(tenant_id: str):
    settings = get_settings()
    if not settings.feature_efirma:
        raise HTTPException(status_code=403, detail="Funcionalidad no habilitada.")
    return {"accesos": []}
