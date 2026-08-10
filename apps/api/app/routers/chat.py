from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ChatMessage(BaseModel):
    contenido: str
    canal: str = "web"


@router.post("/mensaje")
async def send_message(
    msg: ChatMessage,
    tenant_id: str = Query(...),
):
    valid_channels = ["web", "whatsapp_sim"]
    if msg.canal not in valid_channels:
        raise HTTPException(status_code=400, detail=f"Canal debe ser: {valid_channels}")

    return {
        "respuesta": "Funcionalidad de chat requiere configuración de proveedor de IA.",
        "canal": msg.canal,
    }


@router.get("/historial")
async def get_historial(
    tenant_id: str = Query(...),
    canal: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    return {"mensajes": []}
