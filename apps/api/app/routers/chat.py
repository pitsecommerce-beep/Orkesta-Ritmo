from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()

VALID_CHANNELS = ["web", "whatsapp_sim"]


class ChatMessage(BaseModel):
    contenido: str
    canal: str = "web"


@router.post("/mensaje")
async def send_message(
    msg: ChatMessage,
    tenant_id: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if msg.canal not in VALID_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"Canal debe ser: {VALID_CHANNELS}",
        )

    user_msg = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "rol": "user",
        "contenido": msg.contenido,
        "canal": msg.canal,
    }
    resp = db.table("chat_messages").insert(user_msg).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al guardar mensaje.")

    return {
        "mensaje_id": resp.data[0]["id"],
        "respuesta": "Funcionalidad de chat requiere configuración de proveedor de IA.",
        "canal": msg.canal,
    }


@router.get("/historial")
async def get_historial(
    tenant_id: str = Query(...),
    canal: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    query = (
        db.table("chat_messages")
        .select("*")
        .eq("tenant_id", tenant_id)
    )
    if canal:
        query = query.eq("canal", canal)
    query = query.order("created_at", desc=True).limit(limit)
    resp = query.execute()

    return {"mensajes": resp.data}
