from fastapi import APIRouter, Query, HTTPException

router = APIRouter()


@router.post("/ejecutar")
async def ejecutar_calculo(
    tenant_id: str = Query(...),
    periodo_id: str = Query(...),
):
    return {
        "status": "enqueued",
        "message": "Cálculo encolado para procesamiento.",
        "job_id": "placeholder",
    }


@router.get("/resultado/{periodo_id}")
async def get_resultado(periodo_id: str):
    return {
        "periodo_id": periodo_id,
        "estado": "borrador",
        "isr": None,
        "iva": None,
        "alertas": [],
        "trazabilidad": [],
    }


@router.get("/compuertas/{periodo_id}")
async def get_compuertas(periodo_id: str):
    return {
        "puede_calcular": False,
        "bloqueos": [],
    }
