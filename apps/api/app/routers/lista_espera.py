from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import Client

from app.db import get_supabase

router = APIRouter()


class ListaEsperaEntry(BaseModel):
    email: Optional[str] = None
    regimen: str
    rfc: Optional[str] = None


@router.post("/")
async def registrar_espera(
    entry: ListaEsperaEntry,
    db: Client = Depends(get_supabase),
):
    data = {
        "regimen": entry.regimen,
    }
    if entry.email:
        data["email"] = entry.email
    if entry.rfc:
        data["rfc"] = entry.rfc

    resp = db.table("lista_espera").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al registrar en lista de espera.")

    return {
        "status": "registered",
        "regimen": entry.regimen,
        "message": "Te avisaremos cuando soportemos tu régimen fiscal.",
    }
