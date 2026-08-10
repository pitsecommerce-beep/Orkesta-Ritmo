from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_extractos(
    tenant_id: str = Query(...),
):
    return {"extractos": []}


@router.get("/{extracto_id}")
async def get_extracto(extracto_id: str):
    return {"id": extracto_id}


@router.get("/{extracto_id}/movimientos")
async def get_movimientos(
    extracto_id: str,
    solo_espejo: Optional[bool] = None,
    categoria: Optional[str] = None,
):
    return {"movimientos": [], "resumen": {"abono_neto": "0.00", "cargo_neto": "0.00"}}


@router.get("/{extracto_id}/conciliacion")
async def get_conciliacion(extracto_id: str, tenant_id: str = Query(...)):
    return {
        "cobrado_sin_factura": [],
        "facturado_sin_cobro": [],
        "conciliados": [],
    }
