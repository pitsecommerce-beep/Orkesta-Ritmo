from fastapi import APIRouter, Query, UploadFile, File
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_cfdis(
    tenant_id: str = Query(...),
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    sin_actividad: Optional[bool] = None,
    periodo_id: Optional[str] = None,
):
    return {"cfdis": []}


@router.get("/{cfdi_id}")
async def get_cfdi(cfdi_id: str):
    return {"id": cfdi_id}


@router.post("/{cfdi_id}/asignar-actividad")
async def asignar_actividad(cfdi_id: str, actividad_id: str = Query(...)):
    return {"cfdi_id": cfdi_id, "actividad_id": actividad_id, "status": "assigned"}


@router.get("/ppd-pendientes")
async def list_ppd_pendientes(tenant_id: str = Query(...)):
    return {"ppd_pendientes": []}
