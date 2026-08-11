from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from supabase import Client
import re

from app.db import get_supabase, require_auth

router = APIRouter()

REGIMENES_ADMITIDOS = [
    "RESICO_PF", "RESICO_PF_SUELDOS",
    "ARRENDAMIENTO", "ARRENDAMIENTO_SUELDOS",
    "RESICO_PM",
]

RFC_PATTERN = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}$")


class OnboardingStep1(BaseModel):
    nombre: str


class OnboardingStep2(BaseModel):
    tiene_constancia: bool


class OnboardingConstanciaResult(BaseModel):
    rfc: str
    regimen: str
    nombre_constancia: str


class OnboardingStep4(BaseModel):
    origen_ingresos: str


class OnboardingStep5(BaseModel):
    cuentas_bancarias: int


class OnboardingStep6(BaseModel):
    invitar_contador: bool
    email_contador: Optional[str] = None


@router.post("/paso/nombre")
async def paso_nombre(
    data: OnboardingStep1,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    db.table("user_profiles").update({
        "nombre": data.nombre,
    }).eq("id", user_id).execute()

    return {"paso": 1, "siguiente": "constancia"}


@router.post("/paso/constancia")
async def paso_constancia(
    data: OnboardingStep2,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if not data.tiene_constancia:
        return {
            "paso": 2,
            "siguiente": "guia_constancia",
            "guia": {
                "titulo": "Cómo obtener tu Constancia de Situación Fiscal",
                "pasos": [
                    "Ingresa a sat.gob.mx",
                    "Inicia sesión con tu RFC y contraseña",
                    "Ve a 'Otros trámites y servicios' > 'Genera tu Constancia de Situación Fiscal'",
                    "Descarga el PDF",
                    "Súbelo aquí cuando lo tengas",
                ],
                "recordatorio": True,
            },
        }
    return {"paso": 2, "siguiente": "upload_constancia"}


@router.post("/paso/upload-constancia")
async def upload_constancia(
    file: UploadFile = File(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    return {
        "paso": 3,
        "rfc": "XAXX010101000",
        "regimen_detectado": "RESICO_PF",
        "nombre_constancia": "Nombre Extraído",
        "siguiente": "confirmar_regimen",
    }


@router.post("/paso/confirmar-regimen")
async def confirmar_regimen(
    data: OnboardingConstanciaResult,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if not RFC_PATTERN.match(data.rfc):
        raise HTTPException(status_code=400, detail="RFC con formato inválido")

    tipo_persona = "fisica" if len(data.rfc) == 13 else "moral"

    regimen_normalizado = data.regimen.upper().replace(" ", "_")
    if regimen_normalizado not in REGIMENES_ADMITIDOS:
        return {
            "admitido": False,
            "mensaje": f"Por ahora, Ritmo no soporta el régimen {data.regimen}. Te avisaremos cuando esté disponible.",
            "lista_espera": True,
        }

    tenant_data = {
        "rfc": data.rfc,
        "nombre": data.nombre_constancia,
        "tipo_persona": tipo_persona,
        "regimen": regimen_normalizado,
    }
    tenant_resp = db.table("tenants").insert(tenant_data).execute()
    if not tenant_resp.data:
        raise HTTPException(status_code=500, detail="Error al crear contribuyente.")

    tenant_id = tenant_resp.data[0]["id"]

    db.table("memberships").insert({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "rol": "propietario",
    }).execute()

    return {
        "admitido": True,
        "rfc": data.rfc,
        "tipo_persona": tipo_persona,
        "regimen": regimen_normalizado,
        "tenant_id": tenant_id,
        "siguiente": "origen_ingresos",
    }


@router.post("/paso/origen-ingresos")
async def paso_origen(
    data: OnboardingStep4,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    return {"paso": 4, "siguiente": "cuentas_bancarias"}


@router.post("/paso/cuentas-bancarias")
async def paso_cuentas(
    data: OnboardingStep5,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    return {"paso": 5, "siguiente": "invitar_contador"}


@router.post("/paso/invitar-contador")
async def paso_contador(
    data: OnboardingStep6,
    tenant_id: str = None,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if tenant_id:
        db.table("tenants").update({
            "onboarding_completado": True,
        }).eq("id", tenant_id).execute()

    return {
        "paso": 6,
        "onboarding_completado": True,
        "siguiente": "panel",
    }
