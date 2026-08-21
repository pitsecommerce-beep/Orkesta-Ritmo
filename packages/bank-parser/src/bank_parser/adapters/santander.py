"""Adaptador para estados de cuenta de Santander Mexico.

Santander entrega PDFs rasterizados (cero capa de texto), por lo que
este adaptador usa OCR via tesseract. Soporta dos productos:

- Debito (cuenta de cheques): seccion "Detalle de movimientos cuenta de cheques"
- Credito (tarjeta): seccion "CARGOS, ABONOS Y COMPRAS REGULARES"

PENDIENTE DE CONFIRMAR CON CONTADOR: los movimientos de tarjeta de credito
no son equivalentes a flujo de efectivo. El criterio de "efectivamente pagado"
para IVA acreditable tiene reglas propias en TDC. Ademas, el pago del estado
de cuenta desde la cuenta de debito y los cargos de la tarjeta representan
el mismo gasto visto dos veces — riesgo real de duplicar gastos si ambos
documentos se cargan al mismo periodo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bank_parser.ocr import normalizar_texto, ocr_paginas
from bank_parser.types import ExtractoBancario, Movimiento, NivelConfianza

_MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
    "JAN": 1, "APR": 4, "AUG": 8, "DEC": 12,
}

_MESES_LARGO = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5,
    "JUNIO": 6, "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10,
    "NOVIEMBRE": 11, "DICIEMBRE": 12,
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}


def _parse_monto(s: str) -> Decimal:
    """Parse a formatted amount like '8,300.50' or '$ 8,300.50' to Decimal."""
    s = s.replace("$", "").replace(",", "").strip()
    if not s:
        return Decimal("0")
    return Decimal(s)


def _parse_fecha_ddmmmyyyy(s: str) -> date:
    """Parse dates like '04-DIC-2025' or '04-Dic-2025'."""
    s = s.strip().upper()
    m = re.match(r"(\d{1,2})-?([A-Z]{3})-?(\d{4})", s)
    if not m:
        raise ValueError(f"No se pudo parsear fecha: {s!r}")
    dia, mes_str, anio = int(m.group(1)), m.group(2), int(m.group(3))
    mes = _MESES.get(mes_str)
    if mes is None:
        raise ValueError(f"Mes no reconocido: {mes_str!r}")
    return date(anio, mes, dia)


def _parse_fecha_credito(s: str) -> date:
    """Parse credit dates like '12-Nov-2025'."""
    return _parse_fecha_ddmmmyyyy(s)


def _contiene(texto_norm: str, ancla: str) -> bool:
    """Check if normalized text contains normalized anchor."""
    return normalizar_texto(ancla) in texto_norm


def _extraer_rfc(descripcion: str) -> str | None:
    """Extract RFC from movement description if present."""
    m = re.search(r"\bRFC\s+([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})\b", descripcion.upper())
    return m.group(1) if m else None


def _extraer_periodo(texto: str) -> tuple[date | None, date | None]:
    """Extract period dates from header text."""
    norm = normalizar_texto(texto)
    m = re.search(
        r"PERIODO\s+DEL?\s+(\d{1,2})-([A-Z]{3})-(\d{4})\s+AL?\s+(\d{1,2})-([A-Z]{3})-(\d{4})",
        norm,
    )
    if m:
        try:
            inicio = date(int(m.group(3)), _MESES.get(m.group(2), 1), int(m.group(1)))
            fin = date(int(m.group(6)), _MESES.get(m.group(5), 1), int(m.group(4)))
            return inicio, fin
        except (ValueError, KeyError):
            pass
    return None, None


def _extraer_periodo_credito(texto: str) -> tuple[date | None, date | None]:
    """Extract period from credit header like 'Del 13-Nov-2025 al 12-Dic-2025'."""
    norm = normalizar_texto(texto)
    m = re.search(
        r"DEL?\s+(\d{1,2})-([A-Z]{3})-(\d{4})\s+AL?\s+(\d{1,2})-([A-Z]{3})-(\d{4})",
        norm,
    )
    if m:
        try:
            inicio = date(int(m.group(3)), _MESES.get(m.group(2), 1), int(m.group(1)))
            fin = date(int(m.group(6)), _MESES.get(m.group(5), 1), int(m.group(4)))
            return inicio, fin
        except (ValueError, KeyError):
            pass
    return None, None


def _extraer_titular(paginas_texto: list[str]) -> str:
    """Extract account holder name from the bank header page (not advertising)."""
    for texto in paginas_texto:
        norm = normalizar_texto(texto)
        if "SANTANDER" not in norm:
            continue
        if not any(k in norm for k in ["ESTADO DE CUENTA", "TARJETA DE CREDITO", "CODIGO DE CLIENTE"]):
            continue
        for linea in texto.split("\n"):
            linea_stripped = linea.strip()
            if not linea_stripped or len(linea_stripped) < 5:
                continue
            ln = normalizar_texto(linea_stripped)
            skip_keywords = [
                "SANTANDER", "BANCO", "ESTADO DE CUENTA", "INSTITUCION",
                "TARJETA", "CREDITO", "CODIGO", "CALLE", "COLONIA",
                "C.P.", "SUCURSAL", "PERIODO", "CORTE", "NUMERO",
                "RFC", "MONEDA", "CUENTA", "CLABE", "LIMITE",
                "SALDO", "PROMOCION", "CONTRATA", "DOCUMENTO", "RESUMEN",
                "NIVEL", "CARATULA", "PUBLICIT",
            ]
            if any(k in ln for k in skip_keywords):
                # Credit statements have name + "TU PAGO REQUERIDO" on same line
                if "PAGO REQUERIDO" in ln or "TU PAGO" in ln:
                    parts = re.split(r"\s{2,}|TU PAGO", linea_stripped, maxsplit=1)
                    candidate = parts[0].strip()
                    if re.match(r"^[A-ZÁÉÍÓÚÑ\s]+$", candidate) and len(candidate) > 5:
                        return candidate
                continue
            if re.match(r"^[A-ZÁÉÍÓÚÑ\s]+$", linea_stripped):
                return linea_stripped
    return "TITULAR NO IDENTIFICADO"


def _extraer_cuenta(texto: str) -> str:
    """Extract account number or CLABE."""
    m = re.search(r"CLABE[:\s]+(\d[\d\s-]+\d)", texto)
    if m:
        return re.sub(r"[\s-]", "", m.group(1))
    m = re.search(r"(\d{2}-\d{8,}-\d)", texto)
    if m:
        return m.group(1)
    m = re.search(r"Numero de (?:cuenta|tarjeta)[:\s]+([\d\s]+)", texto, re.IGNORECASE)
    if m:
        return re.sub(r"\s", "", m.group(1))
    return ""


# ─── DEBITO ───────────────────────────────────────────────────────────


_RE_FECHA_INICIO_MOV = re.compile(r"^(\d{2}-[A-Z]{3}-\d{4})\s+(\d{5,})\s+(.+)")
_RE_MONTO_LINEA = re.compile(r"([\d,]+\.\d{2})\s*$")
_RE_TOTAL = re.compile(r"^\s*TOTAL\b", re.IGNORECASE)


@dataclass
class _ResumenDebito:
    saldo_inicial: Decimal
    depositos_declarados: Decimal
    retiros_declarados: Decimal
    saldo_final: Decimal


def _parsear_resumen_debito(paginas_texto: list[str]) -> _ResumenDebito:
    """Extract declared summary from the 'Cuenta de cheques' section."""
    saldo_inicial = Decimal("0")
    depositos = Decimal("0")
    retiros = Decimal("0")
    saldo_final = Decimal("0")

    for texto in paginas_texto:
        norm = normalizar_texto(texto)
        if not _contiene(norm, "Saldo inicial"):
            continue
        for linea in texto.split("\n"):
            ln = normalizar_texto(linea)
            montos = re.findall(r"[\d,]+\.\d{2}", linea)
            if not montos:
                continue
            val = _parse_monto(montos[-1])
            if "SALDO INICIAL" in ln:
                saldo_inicial = val
            elif "DEPOSITO" in ln:
                depositos = val
            elif "RETIRO" in ln:
                retiros = val
            elif "SALDO FINAL" in ln:
                saldo_final = val
        break
    return _ResumenDebito(saldo_inicial, depositos, retiros, saldo_final)


def _parsear_movimientos_debito(paginas_texto: list[str]) -> tuple[
    list[Movimiento], Decimal, Decimal, Decimal | None
]:
    """Parse debit movements from OCR pages using semantic anchors.

    Returns (movements, total_depositos, total_retiros, saldo_periodo_anterior).
    """
    en_movimientos = False
    lineas_movimientos: list[str] = []
    saldo_periodo_anterior: Decimal | None = None

    for texto in paginas_texto:
        norm = normalizar_texto(texto)
        if _contiene(norm, "DETALLE DE MOVIMIENTOS CUENTA DE CHEQUES"):
            en_movimientos = True
        if en_movimientos:
            for linea in texto.split("\n"):
                lineas_movimientos.append(linea)
                ln = normalizar_texto(linea)
                if "SALDO FINAL DEL PERIODO ANTERIOR" in ln:
                    montos = re.findall(r"[\d,]+\.\d{2}", linea)
                    if montos:
                        saldo_periodo_anterior = _parse_monto(montos[-1])
            if _contiene(norm, "SALDO FINAL DEL PERIODO:") and en_movimientos:
                break

    movimientos: list[Movimiento] = []
    total_depositos = Decimal("0")
    total_retiros = Decimal("0")

    current_fecha: date | None = None
    current_folio = ""
    current_desc_lines: list[str] = []
    current_deposito: Decimal | None = None
    current_retiro: Decimal | None = None
    current_saldo: Decimal | None = None
    en_tabla = False

    def _flush():
        nonlocal current_fecha, current_folio, current_desc_lines
        nonlocal current_deposito, current_retiro, current_saldo
        if current_fecha is None:
            return
        desc = "\n".join(current_desc_lines).strip()
        dep = current_deposito or Decimal("0")
        ret = current_retiro or Decimal("0")
        monto = dep - ret
        rfc = _extraer_rfc(desc)
        detalle: dict = {}
        if rfc:
            detalle["rfc"] = rfc
        clave_m = re.search(r"CLAVE DE RASTREO\s+(\S+)", desc, re.IGNORECASE)
        if clave_m:
            detalle["clave_rastreo"] = clave_m.group(1)
        ref_m = re.search(r"\bREF\s+(\S+)", desc)
        if ref_m:
            detalle["referencia"] = ref_m.group(1)

        movimientos.append(Movimiento(
            fecha=current_fecha,
            hora=None,
            descripcion=desc,
            identificador_transaccion=current_folio,
            monto=monto,
            comision=Decimal("0"),
            moneda="MXN",
            detalle=detalle,
            confianza=NivelConfianza.ALTA,
        ))
        current_fecha = None
        current_folio = ""
        current_desc_lines = []
        current_deposito = None
        current_retiro = None
        current_saldo = None

    for linea in lineas_movimientos:
        ln_norm = normalizar_texto(linea)

        if "FECHA" in ln_norm and "FOLIO" in ln_norm and "DESCRIPCION" in ln_norm:
            en_tabla = True
            continue

        if not en_tabla:
            continue

        if _RE_TOTAL.match(linea.strip()):
            _flush()
            montos = re.findall(r"[\d,]+\.\d{2}", linea)
            if len(montos) >= 2:
                total_depositos = _parse_monto(montos[0])
                total_retiros = _parse_monto(montos[1])
            elif len(montos) == 1:
                total_depositos = _parse_monto(montos[0])
            break

        if "SALDO FINAL DEL PERIODO:" in ln_norm:
            _flush()
            break

        m = _RE_FECHA_INICIO_MOV.match(linea.strip())
        if m:
            _flush()
            try:
                current_fecha = _parse_fecha_ddmmmyyyy(m.group(1))
            except ValueError:
                continue
            current_folio = m.group(2)
            resto = m.group(3)
            montos = re.findall(r"[\d,]+\.\d{2}", resto)
            desc_part = re.sub(r"[\d,]+\.\d{2}", "", resto).strip()
            current_desc_lines = [desc_part] if desc_part else []

            if len(montos) == 3:
                current_deposito = _parse_monto(montos[0]) if montos[0] != "0" else None
                current_retiro = _parse_monto(montos[1]) if montos[1] != "0" else None
                current_saldo = _parse_monto(montos[2])
            elif len(montos) == 2:
                current_saldo = _parse_monto(montos[-1])
                val = _parse_monto(montos[0])
                if desc_part and any(k in normalizar_texto(desc_part) for k in [
                    "ABONO", "DEPOSITO", "ENLACE",
                ]):
                    current_deposito = val
                else:
                    has_deposit_keyword = False
                    for kw in ["ABONO", "DEPOSITO", "ENLACE"]:
                        if kw in normalizar_texto(desc_part):
                            has_deposit_keyword = True
                    if has_deposit_keyword:
                        current_deposito = val
                    else:
                        current_retiro = val
            elif len(montos) == 1:
                current_saldo = _parse_monto(montos[0])
        elif current_fecha is not None:
            stripped = linea.strip()
            if stripped:
                current_desc_lines.append(stripped)
                montos_extra = re.findall(r"[\d,]+\.\d{2}", stripped)
                if montos_extra and current_deposito is None and current_retiro is None:
                    pass

    _flush()
    return movimientos, total_depositos, total_retiros, saldo_periodo_anterior


def _validar_cuadre_debito(
    movimientos: list[Movimiento],
    resumen: _ResumenDebito,
    total_dep_tabla: Decimal,
    total_ret_tabla: Decimal,
) -> tuple[bool, list[str]]:
    """Validate debit statement balance."""
    alertas: list[str] = []

    sum_dep = sum(m.monto for m in movimientos if m.monto > 0)
    sum_ret = abs(sum(m.monto for m in movimientos if m.monto < 0))

    if sum_dep != resumen.depositos_declarados:
        alertas.append(
            f"Descuadre depositos: extraidos={sum_dep}, "
            f"declarados={resumen.depositos_declarados}, "
            f"diferencia={sum_dep - resumen.depositos_declarados}"
        )
    if sum_ret != resumen.retiros_declarados:
        alertas.append(
            f"Descuadre retiros: extraidos={sum_ret}, "
            f"declarados={resumen.retiros_declarados}, "
            f"diferencia={sum_ret - resumen.retiros_declarados}"
        )

    saldo_calculado = resumen.saldo_inicial + sum_dep - sum_ret
    if saldo_calculado != resumen.saldo_final:
        alertas.append(
            f"Descuadre saldo: calculado={saldo_calculado}, "
            f"declarado={resumen.saldo_final}, "
            f"diferencia={saldo_calculado - resumen.saldo_final}"
        )

    if total_dep_tabla != Decimal("0") and sum_dep != total_dep_tabla:
        alertas.append(
            f"TOTAL depositos tabla ({total_dep_tabla}) != suma movimientos ({sum_dep})"
        )
    if total_ret_tabla != Decimal("0") and sum_ret != total_ret_tabla:
        alertas.append(
            f"TOTAL retiros tabla ({total_ret_tabla}) != suma movimientos ({sum_ret})"
        )

    saldo_corriente = resumen.saldo_inicial
    for i, mov in enumerate(movimientos):
        if mov.monto > 0:
            saldo_corriente += mov.monto
        else:
            saldo_corriente += mov.monto
        saldo_esperado_linea = saldo_corriente
        if mov.detalle.get("saldo_linea") is not None:
            saldo_doc = Decimal(str(mov.detalle["saldo_linea"]))
            if saldo_doc != saldo_esperado_linea:
                alertas.append(
                    f"Ruptura cadena saldos en movimiento {i+1} "
                    f"({mov.fecha}): esperado={saldo_esperado_linea}, "
                    f"documento={saldo_doc}"
                )

    return len(alertas) == 0, alertas


# ─── CREDITO ──────────────────────────────────────────────────────────


_RE_FECHA_CREDITO = re.compile(r"^(\d{2}-[A-Z][a-z]{2}-\d{4})\s+(\d{2}-[A-Z][a-z]{2}-\d{4})\s+(.+)", re.IGNORECASE)
_RE_FECHA_CREDITO_UPPER = re.compile(r"^(\d{2}-[A-Z]{3}-\d{4})\s+(\d{2}-[A-Z]{3}-\d{4})\s+(.+)")


def _parsear_movimientos_credito(paginas_texto: list[str]) -> tuple[
    list[Movimiento], Decimal, Decimal
]:
    """Parse credit card movements using semantic anchors."""
    en_seccion = False
    lineas: list[str] = []

    for texto in paginas_texto:
        norm = normalizar_texto(texto)
        if _contiene(norm, "CARGOS, ABONOS Y COMPRAS REGULARES"):
            en_seccion = True
        if en_seccion:
            for linea in texto.split("\n"):
                lineas.append(linea)
            if _contiene(norm, "TOTAL ABONOS") or _contiene(norm, "TOTAL CARGOS"):
                pass

    movimientos: list[Movimiento] = []
    total_cargos = Decimal("0")
    total_abonos = Decimal("0")
    en_tabla = False

    for linea in lineas:
        ln_norm = normalizar_texto(linea)
        stripped = linea.strip()

        if "FECHA DE LA OPERACION" in ln_norm or "FECHA DE CARGO" in ln_norm:
            en_tabla = True
            continue

        if not en_tabla and not _contiene(ln_norm, "TOTAL CARGOS") and not _contiene(ln_norm, "TOTAL ABONOS"):
            continue

        if _contiene(ln_norm, "TOTAL CARGOS"):
            montos = re.findall(r"[\d,]+\.\d{2}", linea)
            if montos:
                total_cargos = _parse_monto(montos[-1])
            continue

        if _contiene(ln_norm, "TOTAL ABONOS"):
            montos = re.findall(r"[\d,]+\.\d{2}", linea)
            if montos:
                total_abonos = _parse_monto(montos[-1])
            continue

        fecha_m = _RE_FECHA_CREDITO.match(stripped) or _RE_FECHA_CREDITO_UPPER.match(stripped)
        if not fecha_m:
            continue

        try:
            fecha_op = _parse_fecha_ddmmmyyyy(fecha_m.group(1))
            fecha_cargo = _parse_fecha_ddmmmyyyy(fecha_m.group(2))
        except ValueError:
            continue

        resto = fecha_m.group(3)

        signo_m = re.search(r"\s([+-])\s", resto)
        es_abono = False
        if signo_m:
            es_abono = signo_m.group(1) == "-"

        montos = re.findall(r"[\d,]+\.\d{2}", resto)
        if not montos:
            continue
        monto_abs = _parse_monto(montos[-1])

        desc_part = re.sub(r"\s*[+-]\s*\$?\s*[\d,]+\.\d{2}\s*$", "", resto).strip()
        ref_m = re.search(r"([A-Z]{3}\s+\d{9})", desc_part)
        referencia = ref_m.group(1) if ref_m else ""
        if ref_m:
            desc_part = desc_part[:ref_m.start()].strip()

        monto = -monto_abs if es_abono else monto_abs

        detalle: dict = {"fecha_cargo": fecha_cargo.isoformat()}
        if referencia:
            detalle["referencia"] = referencia

        movimientos.append(Movimiento(
            fecha=fecha_op,
            hora=None,
            descripcion=desc_part,
            identificador_transaccion=referencia,
            monto=monto,
            comision=Decimal("0"),
            moneda="MXN",
            detalle=detalle,
            confianza=NivelConfianza.ALTA,
        ))

    return movimientos, total_cargos, total_abonos


def _validar_cuadre_credito(
    movimientos: list[Movimiento],
    total_cargos_declarado: Decimal,
    total_abonos_declarado: Decimal,
) -> tuple[bool, list[str]]:
    """Validate credit statement balance."""
    alertas: list[str] = []

    sum_cargos = sum(m.monto for m in movimientos if m.monto > 0)
    sum_abonos = abs(sum(m.monto for m in movimientos if m.monto < 0))

    if sum_cargos != total_cargos_declarado:
        alertas.append(
            f"Descuadre cargos: extraidos={sum_cargos}, "
            f"declarados={total_cargos_declarado}, "
            f"diferencia={sum_cargos - total_cargos_declarado}"
        )
    if sum_abonos != total_abonos_declarado:
        alertas.append(
            f"Descuadre abonos: extraidos={sum_abonos}, "
            f"declarados={total_abonos_declarado}, "
            f"diferencia={sum_abonos - total_abonos_declarado}"
        )

    return len(alertas) == 0, alertas


# ─── ADAPTADOR ────────────────────────────────────────────────────────


class SantanderAdapter:
    """Adaptador para estados de cuenta Santander Mexico (debito y credito).

    Requiere OCR porque Santander entrega PDFs rasterizados sin capa de texto.
    Detecta automaticamente si el documento es de debito o credito por
    marcadores semanticos, no por numero de pagina.
    """

    institucion: str = "Santander"

    def detecta(self, texto: str) -> bool:
        """Detect Santander from text (pdfplumber or OCR)."""
        norm = normalizar_texto(texto)
        if "SANTANDER" not in norm:
            return False
        return any(k in norm for k in [
            "ESTADO DE CUENTA",
            "CUENTA DE CHEQUES",
            "TARJETA DE CREDITO",
            "DETALLE DE MOVIMIENTOS",
            "CARGOS, ABONOS Y COMPRAS",
            "BANCO SANTANDER MEXICO",
        ])

    def detecta_producto(self, paginas_texto: list[str]) -> str:
        """Detect whether the statement is 'debito' or 'credito'."""
        for texto in paginas_texto:
            norm = normalizar_texto(texto)
            if _contiene(norm, "DETALLE DE MOVIMIENTOS CUENTA DE CHEQUES"):
                return "debito"
            if _contiene(norm, "CUENTA DE CHEQUES"):
                return "debito"
        for texto in paginas_texto:
            norm = normalizar_texto(texto)
            if _contiene(norm, "CARGOS, ABONOS Y COMPRAS REGULARES"):
                return "credito"
            if _contiene(norm, "TARJETA DE CREDITO"):
                return "credito"
        return "desconocido"

    def parsea(self, path: Path) -> ExtractoBancario:
        """Parse a Santander bank statement PDF (rasterized, requires OCR)."""
        paginas_texto = ocr_paginas(path)

        if not paginas_texto or all(not t.strip() for t in paginas_texto):
            raise ValueError(
                "El PDF no produjo texto via OCR. Verifica que tesseract "
                "este instalado y que el archivo sea un estado de cuenta valido."
            )

        producto = self.detecta_producto(paginas_texto)

        if producto == "debito":
            return self._parsear_debito(paginas_texto)
        elif producto == "credito":
            return self._parsear_credito(paginas_texto)
        else:
            raise ValueError(
                "No se pudo determinar si el estado de cuenta Santander es de "
                "debito o credito. Verifique que el PDF contenga las secciones "
                "'Detalle de movimientos cuenta de cheques' o "
                "'CARGOS, ABONOS Y COMPRAS REGULARES'."
            )

    def _parsear_debito(self, paginas_texto: list[str]) -> ExtractoBancario:
        resumen = _parsear_resumen_debito(paginas_texto)
        movimientos, total_dep, total_ret, saldo_anterior = _parsear_movimientos_debito(paginas_texto)

        for mov in movimientos:
            if mov.monto > 0:
                saldo_anterior_mov = (saldo_anterior or resumen.saldo_inicial)
            pass

        saldo_corriente = resumen.saldo_inicial
        for mov in movimientos:
            saldo_corriente += mov.monto
            mov.detalle["saldo_linea"] = str(saldo_corriente)

        cuadra, alertas = _validar_cuadre_debito(
            movimientos, resumen, total_dep, total_ret,
        )

        texto_completo = "\n".join(paginas_texto)
        inicio, fin = _extraer_periodo(texto_completo)
        titular = _extraer_titular(paginas_texto)
        cuenta = _extraer_cuenta(texto_completo)

        return ExtractoBancario(
            institucion="Santander",
            titular=titular,
            identificador_cuenta=cuenta,
            periodo_inicio=inicio or date(2000, 1, 1),
            periodo_fin=fin or date(2000, 1, 1),
            saldo_inicial=resumen.saldo_inicial,
            saldo_final=resumen.saldo_final,
            total_abonos_declarado=resumen.depositos_declarados,
            total_cargos_declarado=resumen.retiros_declarados,
            comisiones_declaradas=Decimal("0"),
            movimientos=movimientos,
            es_confiable=cuadra,
            alertas=alertas,
        )

    def _parsear_credito(self, paginas_texto: list[str]) -> ExtractoBancario:
        movimientos, total_cargos, total_abonos = _parsear_movimientos_credito(paginas_texto)

        cuadra, alertas = _validar_cuadre_credito(
            movimientos, total_cargos, total_abonos,
        )

        texto_completo = "\n".join(paginas_texto)
        inicio, fin = _extraer_periodo_credito(texto_completo)
        titular = _extraer_titular(paginas_texto)
        cuenta = _extraer_cuenta(texto_completo)

        return ExtractoBancario(
            institucion="Santander",
            titular=titular,
            identificador_cuenta=cuenta,
            periodo_inicio=inicio or date(2000, 1, 1),
            periodo_fin=fin or date(2000, 1, 1),
            saldo_inicial=Decimal("0"),
            saldo_final=Decimal("0"),
            total_abonos_declarado=total_abonos,
            total_cargos_declarado=total_cargos,
            comisiones_declaradas=Decimal("0"),
            movimientos=movimientos,
            es_confiable=cuadra,
            alertas=alertas,
        )
