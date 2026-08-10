from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

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
):
    return {"periodos": []}


@router.get("/{periodo_id}")
async def get_periodo(periodo_id: str):
    return {"id": periodo_id}


@router.get("/{periodo_id}/desglose")
async def get_desglose(periodo_id: str):
    return {
        "periodo_id": periodo_id,
        "isr": None,
        "iva": None,
        "trazabilidad": [],
        "alertas": [],
    }


@router.post("/{periodo_id}/marcar-presentado")
async def marcar_presentado(periodo_id: str):
    return {"id": periodo_id, "estado": "presentado"}
