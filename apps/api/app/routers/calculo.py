from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()


@router.post("/ejecutar")
async def ejecutar_calculo(
    tenant_id: str = Query(...),
    periodo_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    periodo_resp = (
        db.table("periodos")
        .select("*")
        .eq("id", periodo_id)
        .eq("tenant_id", tenant_id)
        .single()
        .execute()
    )
    if not periodo_resp.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")

    estado = periodo_resp.data["estado"]
    if estado in ("presentado", "cerrado"):
        raise HTTPException(
            status_code=422,
            detail=f"No se puede recalcular un periodo en estado '{estado}'.",
        )

    return {
        "status": "enqueued",
        "message": "Calculo encolado para procesamiento.",
        "periodo_id": periodo_id,
    }


@router.get("/resultado/{periodo_id}")
async def get_resultado(
    periodo_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("periodos")
        .select("*")
        .eq("id", periodo_id)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")

    periodo = resp.data
    resultado = periodo.get("resultado_json") or {}

    return {
        "periodo_id": periodo_id,
        "estado": periodo["estado"],
        "isr": resultado.get("isr"),
        "iva": resultado.get("iva"),
        "alertas": resultado.get("alertas", []),
        "trazabilidad": resultado.get("trazabilidad", []),
    }


@router.get("/compuertas/{periodo_id}")
async def get_compuertas(
    periodo_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    periodo_resp = (
        db.table("periodos")
        .select("*, tenant_id")
        .eq("id", periodo_id)
        .single()
        .execute()
    )
    if not periodo_resp.data:
        raise HTTPException(status_code=404, detail="Periodo no encontrado.")

    periodo = periodo_resp.data
    tenant_id = periodo["tenant_id"]
    bloqueos = []

    cfdis_resp = (
        db.table("cfdis")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .eq("tipo", "I")
        .execute()
    )
    if (cfdis_resp.count or 0) == 0:
        bloqueos.append("No hay CFDIs de ingreso cargados.")

    sin_actividad_resp = (
        db.table("cfdis")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .eq("tipo", "I")
        .is_("actividad_id", "null")
        .execute()
    )
    if (sin_actividad_resp.count or 0) > 0:
        bloqueos.append(
            f"{sin_actividad_resp.count} CFDIs sin actividad asignada."
        )

    return {
        "puede_calcular": len(bloqueos) == 0,
        "bloqueos": bloqueos,
    }
