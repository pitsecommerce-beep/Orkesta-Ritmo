from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    auth,
    tenants,
    periodos,
    cfdis,
    documentos,
    extractos,
    actividades,
    cuestionario,
    calculo,
    chat,
    boveda,
    onboarding,
    legal,
    intenciones,
    lista_espera,
)

settings = get_settings()

app = FastAPI(
    title="Orkesta Ritmo API",
    description="API para preparación de declaraciones mensuales de impuestos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["tenants"])
app.include_router(periodos.router, prefix="/api/periodos", tags=["periodos"])
app.include_router(cfdis.router, prefix="/api/cfdis", tags=["cfdis"])
app.include_router(documentos.router, prefix="/api/documentos", tags=["documentos"])
app.include_router(extractos.router, prefix="/api/extractos", tags=["extractos"])
app.include_router(actividades.router, prefix="/api/actividades", tags=["actividades"])
app.include_router(cuestionario.router, prefix="/api/cuestionario", tags=["cuestionario"])
app.include_router(calculo.router, prefix="/api/calculo", tags=["calculo"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(boveda.router, prefix="/api/boveda", tags=["boveda"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(legal.router, prefix="/api/legal", tags=["legal"])
app.include_router(intenciones.router, prefix="/api/intenciones", tags=["intenciones"])
app.include_router(lista_espera.router, prefix="/api/lista-espera", tags=["lista-espera"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "orkesta-ritmo-api"}
