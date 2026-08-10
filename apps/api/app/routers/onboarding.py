from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import re

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
async def paso_nombre(data: OnboardingStep1):
    return {"paso": 1, "siguiente": "constancia"}


@router.post("/paso/constancia")
async def paso_constancia(data: OnboardingStep2):
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
async def upload_constancia(file: UploadFile = File(...)):
    return {
        "paso": 3,
        "rfc": "XAXX010101000",
        "regimen_detectado": "RESICO_PF",
        "nombre_constancia": "Nombre Extraído",
        "siguiente": "confirmar_regimen",
    }


@router.post("/paso/confirmar-regimen")
async def confirmar_regimen(data: OnboardingConstanciaResult):
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

    return {
        "admitido": True,
        "rfc": data.rfc,
        "tipo_persona": tipo_persona,
        "regimen": regimen_normalizado,
        "siguiente": "origen_ingresos",
    }


@router.post("/paso/origen-ingresos")
async def paso_origen(data: OnboardingStep4):
    return {"paso": 4, "siguiente": "cuentas_bancarias"}


@router.post("/paso/cuentas-bancarias")
async def paso_cuentas(data: OnboardingStep5):
    return {"paso": 5, "siguiente": "invitar_contador"}


@router.post("/paso/invitar-contador")
async def paso_contador(data: OnboardingStep6):
    return {
        "paso": 6,
        "onboarding_completado": True,
        "siguiente": "panel",
    }
