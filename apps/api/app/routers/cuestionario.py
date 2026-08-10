from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class RespuestaRequest(BaseModel):
    nodo_id: str
    opcion_id: str
    actividad_id: str


@router.get("/nodo/{nodo_id}")
async def get_nodo(nodo_id: str):
    return {"nodo_id": nodo_id, "texto": "", "opciones": [], "tipo": "pregunta"}


@router.post("/responder")
async def responder(respuesta: RespuestaRequest):
    return {
        "siguiente_nodo": None,
        "resultado": None,
        "es_preliminar": True,
    }


@router.get("/grafo")
async def get_grafo_completo():
    return {"nodos": [], "transiciones": []}
