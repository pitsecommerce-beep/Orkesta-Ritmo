from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Optional

router = APIRouter()

ALLOWED_EXTENSIONS = {".xml", ".zip", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Query(...),
    tipo: str = Query(..., description="xml_cfdi, zip_cfdi, estado_cuenta"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión {ext} no permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    return {
        "id": "placeholder",
        "nombre_archivo": file.filename,
        "tipo": tipo,
        "estado": "recibido",
    }


@router.get("/")
async def list_documents(
    tenant_id: str = Query(...),
    estado: Optional[str] = None,
):
    return {"documentos": []}


@router.get("/{documento_id}")
async def get_document(documento_id: str):
    return {"id": documento_id}
