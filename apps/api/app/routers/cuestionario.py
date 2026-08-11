from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from app.db import get_supabase, guest_or_auth

router = APIRouter()


class RespuestaRequest(BaseModel):
    nodo_id: str
    opcion_id: str
    actividad_id: str


@router.get("/nodo/{nodo_id}")
async def get_nodo(
    nodo_id: str,
    db: Client = Depends(get_supabase),
):
    nodo_resp = (
        db.table("cuestionario_nodos")
        .select("*")
        .eq("id", nodo_id)
        .eq("activo", True)
        .single()
        .execute()
    )
    if not nodo_resp.data:
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")

    nodo = nodo_resp.data

    opciones_resp = (
        db.table("cuestionario_opciones")
        .select("*")
        .eq("nodo_id", nodo_id)
        .order("orden")
        .execute()
    )

    return {
        "nodo_id": nodo["id"],
        "texto": nodo["texto"],
        "tipo": nodo["tipo"],
        "resultado": nodo.get("resultado"),
        "opciones": opciones_resp.data,
    }


@router.post("/responder")
async def responder(
    body: RespuestaRequest,
    db: Client = Depends(get_supabase),
):
    trans_resp = (
        db.table("cuestionario_transiciones")
        .select("nodo_destino")
        .eq("nodo_origen", body.nodo_id)
        .eq("opcion_id", body.opcion_id)
        .execute()
    )

    siguiente_nodo = None
    resultado = None

    if trans_resp.data:
        destino_id = trans_resp.data[0]["nodo_destino"]
        destino_resp = (
            db.table("cuestionario_nodos")
            .select("*")
            .eq("id", destino_id)
            .single()
            .execute()
        )
        if destino_resp.data:
            destino = destino_resp.data
            siguiente_nodo = destino["id"]
            if destino["tipo"] == "resultado":
                resultado = destino.get("resultado")

    return {
        "siguiente_nodo": siguiente_nodo,
        "resultado": resultado,
        "actividad_id": body.actividad_id,
    }


@router.get("/grafo")
async def get_grafo(
    db: Client = Depends(get_supabase),
):
    nodos_resp = (
        db.table("cuestionario_nodos")
        .select("*")
        .eq("activo", True)
        .execute()
    )
    trans_resp = (
        db.table("cuestionario_transiciones")
        .select("*")
        .execute()
    )
    return {
        "nodos": nodos_resp.data,
        "transiciones": trans_resp.data,
    }
