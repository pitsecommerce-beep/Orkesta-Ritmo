from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ActividadCreate(BaseModel):
    descripcion: str


class ActividadUpdate(BaseModel):
    descripcion: Optional[str] = None
    resultado: Optional[str] = None


@router.get("/")
async def list_actividades(tenant_id: str = Query(...)):
    return {"actividades": []}


@router.post("/")
async def create_actividad(actividad: ActividadCreate, tenant_id: str = Query(...)):
    return {"id": "placeholder", "descripcion": actividad.descripcion}


@router.patch("/{actividad_id}")
async def update_actividad(actividad_id: str, update: ActividadUpdate):
    return {"id": actividad_id, "updated": True}


@router.get("/{actividad_id}/cobertura")
async def get_cobertura_mapeo(actividad_id: str, tenant_id: str = Query(...)):
    return {
        "total_cfdis": 0,
        "mapeados": 0,
        "sin_mapear": 0,
        "porcentaje": 0.0,
    }
