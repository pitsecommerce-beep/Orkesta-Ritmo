from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ListaEsperaEntry(BaseModel):
    email: Optional[str] = None
    regimen: str
    rfc: Optional[str] = None


@router.post("/")
async def registrar_espera(entry: ListaEsperaEntry):
    return {
        "status": "registered",
        "regimen": entry.regimen,
        "message": "Te avisaremos cuando soportemos tu régimen fiscal.",
    }
