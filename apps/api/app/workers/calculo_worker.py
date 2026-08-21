"""
Worker de calculo fiscal.

Ejecuta el motor de calculo para un periodo dado, usando el catalogo
normativo como fuente de tarifas. Escribe el resultado en la tabla
de periodos y registra la trazabilidad en resolucion_calculo.

No implementa cola RQ — el proyecto no tiene un patron de worker
funcional aun. Esta funcion es invocable directamente desde el router
o desde un futuro worker de cola.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def ejecutar_calculo(tenant_id: str, periodo_id: str, db: Any = None) -> dict:
    """Ejecuta el calculo fiscal para un periodo.

    Args:
        tenant_id: ID del tenant.
        periodo_id: ID del periodo a calcular.
        db: Cliente de Supabase (opcional, para tests sin DB se puede omitir).

    Returns:
        Dict con el resultado del calculo o error.
    """
    from tax_engine.catalogo_adapter import (
        fecha_causacion_de_periodo,
        resolver_ejercicio,
    )
    from tax_engine.catalogo_data import obtener_catalogo
    from tax_engine.engine import calcular
    from tax_engine.exceptions import (
        EjercicioNoDisponibleError,
        RegimenEnValidacionError,
    )
    from tax_engine.types import CfdiNormalizado, PerfilFiscal, Regimen

    if db is None:
        return {"error": "No hay conexion a base de datos."}

    try:
        periodo_resp = (
            db.table("periodos")
            .select("*")
            .eq("id", periodo_id)
            .eq("tenant_id", tenant_id)
            .single()
            .execute()
        )
        if not periodo_resp.data:
            return {"error": f"Periodo {periodo_id} no encontrado."}
        periodo = periodo_resp.data

        tenant_resp = (
            db.table("tenants")
            .select("regimen, rfc, tipo_deduccion, opcion_trimestral")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        if not tenant_resp.data:
            return {"error": f"Tenant {tenant_id} no encontrado."}
        tenant = tenant_resp.data

        regimen_str = tenant.get("regimen", "")
        try:
            regimen = Regimen(regimen_str)
        except ValueError:
            return {"error": f"Regimen no soportado: {regimen_str}"}

        perfil = PerfilFiscal(
            regimen=regimen,
            rfc=tenant.get("rfc", ""),
            tipo_deduccion=tenant.get("tipo_deduccion", "opcional"),
            opcion_trimestral=tenant.get("opcion_trimestral", False),
        )

        ejercicio_year = periodo["ejercicio"]
        numero_periodo = periodo["numero_periodo"]
        trimestral = perfil.opcion_trimestral

        catalogo = obtener_catalogo()
        fecha_caus = fecha_causacion_de_periodo(
            ejercicio_year, numero_periodo, trimestral=trimestral,
        )
        ejercicio_resuelto = resolver_ejercicio(catalogo, fecha_caus)

        cfdis_resp = (
            db.table("cfdis")
            .select("*")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        cfdis_emitidos = _mapear_cfdis(cfdis_resp.data or [])

    except (EjercicioNoDisponibleError, RegimenEnValidacionError) as exc:
        _marcar_requiere_revision(db, periodo_id, tenant_id, str(exc))
        return {"error": str(exc), "estado": "requiere_revision"}
    except Exception as exc:
        logger.exception("Error preparando calculo para periodo %s", periodo_id)
        return {"error": f"Error inesperado: {exc}"}

    try:
        resultado = calcular(
            cfdis_emitidos=cfdis_emitidos,
            perfil=perfil,
            ejercicio_year=ejercicio_year,
            periodo=numero_periodo,
            ejercicio=ejercicio_resuelto.ejercicio,
        )
    except (EjercicioNoDisponibleError, RegimenEnValidacionError) as exc:
        _marcar_requiere_revision(db, periodo_id, tenant_id, str(exc))
        return {"error": str(exc), "estado": "requiere_revision"}

    resultado_json = {
        "isr": {
            "ingresos": str(resultado.isr.ingresos),
            "deducciones": str(resultado.isr.deducciones),
            "base_gravable": str(resultado.isr.base_gravable),
            "impuesto_determinado": str(resultado.isr.impuesto_determinado),
            "retenciones_isr": str(resultado.isr.retenciones_isr),
            "isr_a_cargo": str(resultado.isr.isr_a_cargo),
        },
        "iva": {
            "iva_trasladado": str(resultado.iva.iva_trasladado),
            "iva_retenido": str(resultado.iva.iva_retenido),
            "iva_acreditable": str(resultado.iva.iva_acreditable),
            "iva_a_pagar": str(resultado.iva.iva_a_pagar),
        },
        "alertas": resultado.alertas,
        "estado": resultado.estado,
    }

    try:
        db.table("periodos").update({
            "estado": resultado.estado,
            "resultado_json": resultado_json,
        }).eq("id", periodo_id).execute()
    except Exception:
        logger.exception("Error actualizando periodo %s", periodo_id)

    _registrar_resolucion(
        db=db,
        tenant_id=tenant_id,
        ejercicio_year=ejercicio_year,
        numero_periodo=numero_periodo,
        regimen=regimen_str,
        fecha_causacion=fecha_caus,
        metadata=ejercicio_resuelto.metadata,
        resultado_json=resultado_json,
    )

    return {"estado": resultado.estado, "resultado": resultado_json}


def _marcar_requiere_revision(
    db: Any, periodo_id: str, tenant_id: str, motivo: str,
) -> None:
    try:
        db.table("periodos").update({
            "estado": "requiere_revision",
            "resultado_json": {"error": motivo},
        }).eq("id", periodo_id).execute()
    except Exception:
        logger.exception(
            "Error marcando periodo %s como requiere_revision", periodo_id,
        )


def _registrar_resolucion(
    db: Any,
    tenant_id: str,
    ejercicio_year: int,
    numero_periodo: int,
    regimen: str,
    fecha_causacion: date,
    metadata: Any,
    resultado_json: dict,
) -> None:
    try:
        registro = {
            "tenant_id": tenant_id,
            "ejercicio": ejercicio_year,
            "periodo": numero_periodo,
            "regimen": regimen,
            "fecha_causacion": fecha_causacion.isoformat(),
            "reglas_usadas": json.loads(json.dumps(
                metadata.reglas_usadas, cls=_DecimalEncoder,
            )),
            "tarifas_usadas": json.loads(json.dumps(
                metadata.tarifas_usadas, cls=_DecimalEncoder,
            )),
            "indicadores_usados": json.loads(json.dumps(
                metadata.indicadores_usados, cls=_DecimalEncoder,
            )),
            "resultado_json": resultado_json,
            "version_motor": "1.0.0",
        }
        db.table("resolucion_calculo").insert(registro).execute()
    except Exception:
        logger.exception(
            "Error registrando resolucion_calculo para periodo %s (ej %s)",
            numero_periodo, ejercicio_year,
        )


def _mapear_cfdis(cfdis_raw: list[dict]) -> list:
    from tax_engine.types import (
        CfdiNormalizado,
        ImpuestoRetenido,
        ImpuestoTrasladado,
    )

    resultado = []
    for c in cfdis_raw:
        trasladados = []
        for t in (c.get("impuestos_trasladados") or []):
            trasladados.append(ImpuestoTrasladado(
                impuesto=t.get("impuesto", ""),
                tasa=Decimal(str(t.get("tasa", "0"))),
                importe=Decimal(str(t.get("importe", "0"))),
                base=Decimal(str(t.get("base", "0"))),
            ))
        retenidos = []
        for r in (c.get("impuestos_retenidos") or []):
            retenidos.append(ImpuestoRetenido(
                impuesto=r.get("impuesto", ""),
                tasa=Decimal(str(r.get("tasa", "0"))),
                importe=Decimal(str(r.get("importe", "0"))),
            ))
        resultado.append(CfdiNormalizado(
            uuid=c.get("uuid", ""),
            tipo=c.get("tipo", "I"),
            metodo_pago=c.get("metodo_pago", "PUE"),
            fecha_emision=c.get("fecha_emision", ""),
            fecha_pago=c.get("fecha_pago"),
            rfc_emisor=c.get("rfc_emisor", ""),
            rfc_receptor=c.get("rfc_receptor", ""),
            subtotal=Decimal(str(c.get("subtotal", "0"))),
            total=Decimal(str(c.get("total", "0"))),
            impuestos_trasladados=trasladados,
            impuestos_retenidos=retenidos,
            estado=c.get("estado", "vigente"),
            objeto_imp=c.get("objeto_imp", "02"),
        ))
    return resultado
