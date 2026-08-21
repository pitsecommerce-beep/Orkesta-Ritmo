"""Worker de procesamiento de documentos.

Segun el tipo de documento:
- xml_cfdi / zip_cfdi: invoca cfdi_parser para extraer datos del XML
- estado_cuenta: invoca bank_parser para extraer movimientos bancarios

Persiste los resultados en las tablas correspondientes y actualiza
el estado del documento a 'validado' o 'con_error'.

NOTA: No hay cola RQ funcional. Se invoca sincronamente via
BackgroundTasks de FastAPI. Deuda tecnica anotada en PENDIENTES.md.
"""

from __future__ import annotations

import logging
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def procesar_documento(
    documento_id: str,
    tenant_id: str,
    tipo: str,
    contenido: bytes,
    nombre_archivo: str,
    db: Any,
) -> dict:
    """Procesa un documento segun su tipo.

    Args:
        documento_id: ID del documento en la tabla documentos.
        tenant_id: ID del tenant propietario.
        tipo: Uno de 'xml_cfdi', 'zip_cfdi', 'estado_cuenta'.
        contenido: Bytes crudos del archivo.
        nombre_archivo: Nombre original del archivo.
        db: Cliente de Supabase.

    Returns:
        Dict con el resultado del procesamiento.
    """
    try:
        _actualizar_estado(db, documento_id, "procesando")

        if tipo in ("xml_cfdi", "zip_cfdi"):
            resultado = _procesar_cfdi(
                documento_id, tenant_id, tipo, contenido, nombre_archivo, db,
            )
        elif tipo == "estado_cuenta":
            resultado = _procesar_estado_cuenta(
                documento_id, tenant_id, contenido, nombre_archivo, db,
            )
        else:
            raise ValueError(f"Tipo de documento no soportado: {tipo}")

        _actualizar_estado(db, documento_id, "validado", metadata=resultado)
        return resultado

    except Exception as exc:
        logger.exception(
            "Error procesando documento %s (tipo=%s)", documento_id, tipo,
        )
        error_msg = str(exc)
        _actualizar_estado(
            db, documento_id, "con_error",
            metadata={"error": error_msg},
        )
        return {"error": error_msg}


def _actualizar_estado(
    db: Any, documento_id: str, estado: str, metadata: dict | None = None,
) -> None:
    update_data: dict = {"estado": estado}
    if metadata is not None:
        update_data["metadata"] = metadata
    try:
        db.table("documentos").update(update_data).eq("id", documento_id).execute()
    except Exception:
        logger.exception("Error actualizando estado de documento %s", documento_id)


def _procesar_cfdi(
    documento_id: str,
    tenant_id: str,
    tipo: str,
    contenido: bytes,
    nombre_archivo: str,
    db: Any,
) -> dict:
    from cfdi_parser.source import detect_and_parse, ManualUploadSource

    if tipo == "zip_cfdi":
        source = ManualUploadSource([(nombre_archivo, contenido)])
        from datetime import date
        resultados = source.fetch("", date.min, date.max)
    else:
        resultados = [detect_and_parse(contenido)]

    cfdis_insertados = 0
    errores: list[str] = []

    for r in resultados:
        if not r.es_valido or r.data is None:
            errores.extend(r.errores)
            continue

        data = r.data
        cfdi_data = {
            "tenant_id": tenant_id,
            "documento_id": documento_id,
            "uuid_fiscal": getattr(data, "uuid", ""),
            "tipo": getattr(data, "tipo_comprobante", "I"),
            "metodo_pago": getattr(data, "metodo_pago", "PUE"),
            "fecha_emision": str(getattr(data, "fecha_emision", "")),
            "rfc_emisor": getattr(data, "rfc_emisor", ""),
            "rfc_receptor": getattr(data, "rfc_receptor", ""),
            "subtotal": str(getattr(data, "subtotal", "0")),
            "total": str(getattr(data, "total", "0")),
            "moneda": getattr(data, "moneda", "MXN"),
            "estado": "vigente",
        }

        fecha_pago = getattr(data, "fecha_pago", None)
        if fecha_pago:
            cfdi_data["fecha_pago"] = str(fecha_pago)

        try:
            resp = db.table("cfdis").insert(cfdi_data).execute()
            if resp.data:
                cfdi_id = resp.data[0]["id"]
                _insertar_impuestos(db, cfdi_id, tenant_id, data)
                cfdis_insertados += 1
        except Exception as exc:
            errores.append(f"Error insertando CFDI: {exc}")

    return {
        "cfdis_insertados": cfdis_insertados,
        "errores": errores,
    }


def _insertar_impuestos(db: Any, cfdi_id: str, tenant_id: str, data: Any) -> None:
    trasladados = getattr(data, "impuestos_trasladados", None) or []
    for imp in trasladados:
        try:
            db.table("cfdi_impuestos").insert({
                "cfdi_id": cfdi_id,
                "tenant_id": tenant_id,
                "tipo": "trasladado",
                "impuesto": getattr(imp, "impuesto", ""),
                "tasa_o_cuota": str(getattr(imp, "tasa_o_cuota", "0")),
                "importe": str(getattr(imp, "importe", "0")),
                "base": str(getattr(imp, "base", "0")),
            }).execute()
        except Exception:
            logger.warning("Error insertando impuesto trasladado para CFDI %s", cfdi_id)

    retenidos = getattr(data, "impuestos_retenidos", None) or []
    for imp in retenidos:
        try:
            db.table("cfdi_impuestos").insert({
                "cfdi_id": cfdi_id,
                "tenant_id": tenant_id,
                "tipo": "retenido",
                "impuesto": getattr(imp, "impuesto", ""),
                "tasa_o_cuota": str(getattr(imp, "tasa_o_cuota", "0")),
                "importe": str(getattr(imp, "importe", "0")),
            }).execute()
        except Exception:
            logger.warning("Error insertando impuesto retenido para CFDI %s", cfdi_id)


def _procesar_estado_cuenta(
    documento_id: str,
    tenant_id: str,
    contenido: bytes,
    nombre_archivo: str,
    db: Any,
) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contenido)
        tmp_path = Path(tmp.name)

    try:
        from bank_parser.detector import parsea_estado_de_cuenta
        extracto = parsea_estado_de_cuenta(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    extracto_data = {
        "tenant_id": tenant_id,
        "documento_id": documento_id,
        "institucion": extracto.institucion,
        "titular": extracto.titular,
        "identificador_cuenta": extracto.identificador_cuenta,
        "periodo_inicio": extracto.periodo_inicio.isoformat(),
        "periodo_fin": extracto.periodo_fin.isoformat(),
        "saldo_inicial": str(extracto.saldo_inicial),
        "saldo_final": str(extracto.saldo_final),
        "total_abonos_declarado": str(extracto.total_abonos_declarado),
        "total_cargos_declarado": str(extracto.total_cargos_declarado),
        "comisiones_declaradas": str(extracto.comisiones_declaradas),
        "es_confiable": extracto.es_confiable,
        "alertas": extracto.alertas,
    }

    try:
        resp = db.table("extractos_bancarios").insert(extracto_data).execute()
        extracto_id = resp.data[0]["id"] if resp.data else None
    except Exception as exc:
        raise ValueError(f"Error insertando extracto bancario: {exc}") from exc

    if extracto_id:
        movs_insertados = 0
        for mov in extracto.movimientos:
            try:
                db.table("movimientos_bancarios").insert({
                    "extracto_id": extracto_id,
                    "tenant_id": tenant_id,
                    "fecha": mov.fecha.isoformat(),
                    "descripcion": mov.descripcion,
                    "identificador_transaccion": mov.identificador_transaccion,
                    "monto": str(mov.monto),
                    "comision": str(mov.comision),
                    "moneda": mov.moneda,
                    "detalle": mov.detalle,
                    "es_espejo": mov.es_espejo,
                    "confianza": mov.confianza.value,
                }).execute()
                movs_insertados += 1
            except Exception:
                logger.warning(
                    "Error insertando movimiento para extracto %s", extracto_id,
                )

    estado_cuadre = "confiable" if extracto.es_confiable else "requiere_revision"

    return {
        "extracto_id": extracto_id,
        "institucion": extracto.institucion,
        "movimientos_insertados": movs_insertados,
        "es_confiable": extracto.es_confiable,
        "alertas": extracto.alertas,
        "estado_cuadre": estado_cuadre,
    }
