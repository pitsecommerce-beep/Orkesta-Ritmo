from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()


@router.get("/")
async def list_extractos(
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("extractos_bancarios")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("periodo_inicio", desc=True)
        .execute()
    )
    return {"extractos": resp.data}


@router.get("/{extracto_id}")
async def get_extracto(
    extracto_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("extractos_bancarios")
        .select("*")
        .eq("id", extracto_id)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Extracto no encontrado.")
    return resp.data


@router.get("/{extracto_id}/movimientos")
async def get_movimientos(
    extracto_id: str,
    solo_espejo: Optional[bool] = None,
    categoria: Optional[str] = None,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    query = (
        db.table("movimientos_bancarios")
        .select("*")
        .eq("extracto_id", extracto_id)
    )
    if solo_espejo is not None:
        query = query.eq("es_espejo", solo_espejo)
    if categoria:
        query = query.eq("categoria", categoria)
    query = query.order("fecha").order("id")
    resp = query.execute()

    movimientos = resp.data
    abono_neto = sum(
        Decimal(str(m["monto"])) for m in movimientos
        if Decimal(str(m["monto"])) > 0 and not m.get("es_espejo")
    )
    cargo_neto = sum(
        Decimal(str(m["monto"])) for m in movimientos
        if Decimal(str(m["monto"])) < 0 and not m.get("es_espejo")
    )

    return {
        "movimientos": movimientos,
        "resumen": {
            "abono_neto": str(abono_neto),
            "cargo_neto": str(cargo_neto),
        },
    }


@router.get("/{extracto_id}/conciliacion")
async def get_conciliacion(
    extracto_id: str,
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = (
        db.table("conciliaciones")
        .select("*")
        .eq("tenant_id", tenant_id)
        .execute()
    )
    data = resp.data

    cobrado_sin_factura = [r for r in data if r["tipo"] == "cobrado_sin_factura"]
    facturado_sin_cobro = [r for r in data if r["tipo"] == "facturado_sin_cobro"]
    conciliados = [r for r in data if r["tipo"] == "conciliado"]

    return {
        "cobrado_sin_factura": cobrado_sin_factura,
        "facturado_sin_cobro": facturado_sin_cobro,
        "conciliados": conciliados,
    }
