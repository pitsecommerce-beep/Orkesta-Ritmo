from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File
from typing import Optional
from supabase import Client

from app.db import get_supabase, require_auth

router = APIRouter()

ALLOWED_EXTENSIONS = {".xml", ".zip", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tenant_id: str = Query(...),
    tipo: str = Query(...),
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    if tipo not in ("xml_cfdi", "zip_cfdi", "estado_cuenta"):
        raise HTTPException(status_code=422, detail="Tipo debe ser xml_cfdi, zip_cfdi o estado_cuenta.")

    if not file.filename:
        raise HTTPException(status_code=422, detail="Archivo sin nombre.")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Extension '{ext}' no permitida. Permitidas: {ALLOWED_EXTENSIONS}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo excede 50 MB.")

    import hashlib
    sha256 = hashlib.sha256(content).hexdigest()

    storage_path = f"{tenant_id}/{sha256}{ext}"

    doc_data = {
        "tenant_id": tenant_id,
        "nombre_archivo": file.filename,
        "tipo": tipo,
        "estado": "recibido",
        "storage_path": storage_path,
        "tamano_bytes": len(content),
        "hash_sha256": sha256,
    }
    resp = db.table("documentos").insert(doc_data).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Error al registrar documento.")

    documento = resp.data[0]

    from app.workers.documento_worker import procesar_documento
    background_tasks.add_task(
        procesar_documento,
        documento_id=documento["id"],
        tenant_id=tenant_id,
        tipo=tipo,
        contenido=content,
        nombre_archivo=file.filename,
        db=db,
    )

    return {
        **documento,
        "status": "processing",
        "message": "Documento recibido. El procesamiento se ejecuta en segundo plano.",
    }


@router.get("/")
async def list_documentos(
    tenant_id: str = Query(...),
    estado: Optional[str] = None,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    query = db.table("documentos").select("*").eq("tenant_id", tenant_id)
    if estado:
        query = query.eq("estado", estado)
    query = query.order("created_at", desc=True)
    resp = query.execute()
    return {"documentos": resp.data}


@router.get("/{documento_id}")
async def get_documento(
    documento_id: str,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(require_auth),
):
    resp = db.table("documentos").select("*").eq("id", documento_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return resp.data
