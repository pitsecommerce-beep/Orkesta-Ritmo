"""Adaptador para estados de cuenta de Mercado Pago Mexico.

Formato real de pdfplumber: movimientos en dos lineas.
  Linea 1: DD/MM/YYYY Tipo - Descripcion
  Linea 2: HH:MM:SS  id_transaccion  monto  comision  MONEDA

Hallazgos verificados de estados de cuenta reales (Octubre 2025):

1. La formula de saldo NO cuadra en Mercado Pago. El invariante correcto es:
   suma de movimientos parseados == totales declarados en el encabezado (al centavo).

2. Movimientos espejo: pares con el mismo ID de transaccion y montos exactamente
   opuestos. Son movimientos internos, NO ingreso. Sin esta regla el ingreso se
   sobreestima hasta un 68%.

3. Las comisiones de los movimientos contradicen el total declarado en el
   encabezado. Se marcan como NO_CONFIABLE.

4. "Cargo - Dinero retenido" son retenciones temporales de fondos, no gastos.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pdfplumber

from bank_parser.types import ExtractoBancario, Movimiento, NivelConfianza

# ---------------------------------------------------------------------------
# Catalogo de descripciones conocidas
# ---------------------------------------------------------------------------
DESCRIPCIONES_CONOCIDAS: set[str] = {
    "Transferencia recibida",
    "Transferencia enviada",
    "Pago",
    "Cobro automatico por deuda",
    "Devolucion de dinero",
    "Dinero retenido",
    "Cashback recibido",
    "Entrada de dinero",
    "Cancelacion de transferencia recibida",
}

_VARIANTES_TILDE: dict[str, str] = {
    "cobro automático por deuda": "Cobro automatico por deuda",
    "devolución de dinero": "Devolucion de dinero",
    "cancelación de transferencia recibida": "Cancelacion de transferencia recibida",
}

_PREFIJOS_TIPO = ("Abono - ", "Cargo - ")

CATEGORIA_RETENCION = "retencion_temporal"
CATEGORIA_COMISION = "comision"

# ---------------------------------------------------------------------------
# Patrones regex
# ---------------------------------------------------------------------------

# Linea 1 de movimiento: DD/MM/YYYY  Tipo - Descripcion
_RE_LINEA1 = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s*$")

# Linea 2 de movimiento: HH:MM:SS  id_transaccion  monto  comision  MONEDA
_RE_LINEA2 = re.compile(
    r"^(\d{2}:\d{2}:\d{2})\s+"
    r"(\d+)\s+"
    r"(-?[\d,]+\.\d{2})\s+"
    r"(-?[\d,]+\.\d{2})\s+"
    r"([A-Z]{3})\s*$"
)

# Formato legacy de una sola linea (backward compat)
_RE_LEGACY = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+"
    r"(\d{2}:\d{2}:\d{2})?\s*"
    r"(.+?)\s+"
    r"(\d+)\s+"
    r"(-?[\d,]+\.\d{2})\s+"
    r"(-?[\d,]+\.\d{2})\s+"
    r"([A-Z]{3})\s*$"
)

# SPEI
_RE_SPEI_CLAVE = re.compile(r"Clave de rastreo[:\s]+(\S+)", re.IGNORECASE)
_RE_SPEI_CLABE = re.compile(r"CLABE[:\s]+(\d{18})", re.IGNORECASE)
_RE_SPEI_BENEFICIARIO = re.compile(
    r"(?:Beneficiario|Ordenante)[:\s]+(.+)", re.IGNORECASE
)

# Encabezado
_RE_TOTAL_ABONOS = re.compile(
    r"Total\s+de\s+abonos[:\s]*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE
)
_RE_TOTAL_CARGOS = re.compile(
    r"Total\s+de\s+cargos[:\s]*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE
)
_RE_SALDO_INICIAL = re.compile(
    r"Saldo\s+inicial[:\s]*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE
)
_RE_SALDO_FINAL = re.compile(
    r"Saldo\s+final[:\s]*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE
)
_RE_COMISIONES = re.compile(
    r"(?:Total\s+de\s+)?[Cc]omisiones[:\s]*\$?\s*([\d,]+\.\d{2})", re.IGNORECASE
)
_RE_PERIODO = re.compile(
    r"(?:Per[ií]odo|Periodo)[:\s]+(\d{2}/\d{2}/\d{4})\s+(?:al?|a|-)\s+(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
_RE_TITULAR = re.compile(r"(?:Titular|Nombre)[:\s]+(.+)", re.IGNORECASE)
_RE_CUENTA = re.compile(r"(?:CVU|Cuenta|CLABE)[:\s]+(\d+)", re.IGNORECASE)


def _parsea_decimal(texto: str) -> Decimal:
    limpio = texto.strip().replace("$", "").replace(",", "").replace(" ", "")
    try:
        return Decimal(limpio)
    except InvalidOperation:
        raise ValueError(f"No se puede convertir a Decimal: {texto!r}")


def _parsea_fecha(texto: str) -> date:
    partes = texto.strip().split("/")
    if len(partes) != 3:
        raise ValueError(f"Formato de fecha invalido: {texto!r}")
    dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
    return date(anio, mes, dia)


def _parsea_hora(texto: str) -> Optional[time]:
    if not texto or not texto.strip():
        return None
    partes = texto.strip().split(":")
    if len(partes) != 3:
        return None
    return time(int(partes[0]), int(partes[1]), int(partes[2]))


def _enmascara_nombre(nombre: str) -> str:
    if not nombre or not nombre.strip():
        return "***"
    palabras = nombre.strip().split()
    return " ".join(p[0] + "***" for p in palabras if p)


def _enmascara_cuenta(cuenta: str) -> str:
    if not cuenta or len(cuenta) < 4:
        return "****"
    return "*" * (len(cuenta) - 4) + cuenta[-4:]


def _normaliza_descripcion(descripcion: str) -> tuple[str, str]:
    texto = descripcion.strip()
    tipo = "otro"

    for prefijo in _PREFIJOS_TIPO:
        if texto.startswith(prefijo):
            tipo = "abono" if "Abono" in prefijo else "cargo"
            texto = texto[len(prefijo):]
            break

    texto_lower = texto.lower().strip()
    if texto_lower in _VARIANTES_TILDE:
        texto = _VARIANTES_TILDE[texto_lower]

    for conocida in DESCRIPCIONES_CONOCIDAS:
        if texto.lower() == conocida.lower():
            texto = conocida
            break

    return tipo, texto


class MercadoPagoAdapter:
    """Adaptador para estados de cuenta de Mercado Pago Mexico.

    Soporta dos formatos de texto extraido:
    - Formato real (dos lineas por movimiento): fecha+descripcion / hora+id+monto+comision+moneda
    - Formato legacy (una linea por movimiento): fecha hora descripcion id monto comision moneda
    """

    institucion: str = "Mercado Pago"

    def detecta(self, texto: str) -> bool:
        texto_lower = texto.lower()
        marcadores = ["mercado pago", "mercadopago", "mercado libre"]
        tiene_marcador = any(m in texto_lower for m in marcadores)
        tiene_formato = any(
            t in texto_lower
            for t in [
                "estado de cuenta",
                "extracto",
                "saldo inicial",
                "total de abonos",
                "movimientos",
            ]
        )
        return tiene_marcador and tiene_formato

    def parsea(self, path: Path) -> ExtractoBancario:
        texto_completo = self._extrae_texto(path)
        return self._parsea_texto(texto_completo)

    def _extrae_texto(self, path: Path) -> str:
        with pdfplumber.open(path) as pdf:
            paginas = []
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    paginas.append(texto)
        return "\n".join(paginas)

    def _parsea_texto(self, texto_completo: str) -> ExtractoBancario:
        lineas = texto_completo.split("\n")
        encabezado = self._parsea_encabezado(texto_completo)
        movimientos = self._parsea_movimientos(lineas)

        extracto = ExtractoBancario(
            institucion=self.institucion,
            titular=encabezado["titular"],
            identificador_cuenta=encabezado["cuenta"],
            periodo_inicio=encabezado["periodo_inicio"],
            periodo_fin=encabezado["periodo_fin"],
            saldo_inicial=encabezado["saldo_inicial"],
            saldo_final=encabezado["saldo_final"],
            total_abonos_declarado=encabezado["total_abonos"],
            total_cargos_declarado=encabezado["total_cargos"],
            comisiones_declaradas=encabezado["comisiones"],
            movimientos=movimientos,
            es_confiable=True,
            alertas=[],
        )

        self._detecta_espejos(extracto)
        self._valida_totales(extracto)
        self._valida_comisiones(extracto)
        self._clasifica_movimientos(extracto)
        self._verifica_descripciones(extracto)

        return extracto

    def _parsea_encabezado(self, texto: str) -> dict:
        resultado = {
            "titular": "***",
            "cuenta": "****",
            "periodo_inicio": date(2000, 1, 1),
            "periodo_fin": date(2000, 1, 1),
            "saldo_inicial": Decimal("0"),
            "saldo_final": Decimal("0"),
            "total_abonos": Decimal("0"),
            "total_cargos": Decimal("0"),
            "comisiones": Decimal("0"),
        }

        match = _RE_TITULAR.search(texto)
        if match:
            resultado["titular"] = _enmascara_nombre(match.group(1))

        match = _RE_CUENTA.search(texto)
        if match:
            resultado["cuenta"] = _enmascara_cuenta(match.group(1))

        match = _RE_PERIODO.search(texto)
        if match:
            resultado["periodo_inicio"] = _parsea_fecha(match.group(1))
            resultado["periodo_fin"] = _parsea_fecha(match.group(2))

        match = _RE_SALDO_INICIAL.search(texto)
        if match:
            resultado["saldo_inicial"] = _parsea_decimal(match.group(1))

        match = _RE_SALDO_FINAL.search(texto)
        if match:
            resultado["saldo_final"] = _parsea_decimal(match.group(1))

        match = _RE_TOTAL_ABONOS.search(texto)
        if match:
            resultado["total_abonos"] = _parsea_decimal(match.group(1))

        match = _RE_TOTAL_CARGOS.search(texto)
        if match:
            resultado["total_cargos"] = _parsea_decimal(match.group(1))

        match = _RE_COMISIONES.search(texto)
        if match:
            resultado["comisiones"] = _parsea_decimal(match.group(1))

        return resultado

    def _parsea_movimientos(self, lineas: list[str]) -> list[Movimiento]:
        movimientos: list[Movimiento] = []
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()

            # Try two-line format: line 1 = date + description
            m1 = _RE_LINEA1.match(linea)
            if m1 and i + 1 < len(lineas):
                linea2 = lineas[i + 1].strip()
                m2 = _RE_LINEA2.match(linea2)
                if m2:
                    mov = self._construye_movimiento_dos_lineas(m1, m2)
                    if mov is not None:
                        detalle = {}
                        j = i + 2
                        while j < len(lineas) and j <= i + 6:
                            ld = lineas[j].strip()
                            if _RE_LINEA1.match(ld):
                                break
                            if self._es_linea_legacy(ld):
                                break
                            spei = self._extrae_spei(ld)
                            if spei:
                                detalle.update(spei)
                                j += 1
                            else:
                                break

                        if detalle:
                            if "clabe" in detalle:
                                detalle["clabe"] = _enmascara_cuenta(detalle["clabe"])
                            mov.detalle = detalle

                        movimientos.append(mov)
                        i = j
                        continue

            # Try legacy single-line format
            mov = self._intenta_parsear_legacy(linea)
            if mov is not None:
                detalle = {}
                j = i + 1
                while j < len(lineas) and j <= i + 5:
                    ld = lineas[j].strip()
                    if self._es_linea_legacy(ld):
                        break
                    spei = self._extrae_spei(ld)
                    if spei:
                        detalle.update(spei)
                        j += 1
                    else:
                        break

                if detalle:
                    if "clabe" in detalle:
                        detalle["clabe"] = _enmascara_cuenta(detalle["clabe"])
                    mov.detalle = detalle

                movimientos.append(mov)
                i = j if detalle else i + 1
            else:
                i += 1

        return movimientos

    def _construye_movimiento_dos_lineas(
        self, m1: re.Match, m2: re.Match
    ) -> Optional[Movimiento]:
        fecha_str = m1.group(1)
        descripcion_raw = m1.group(2).strip()

        hora_str = m2.group(1)
        id_transaccion = m2.group(2)
        monto_str = m2.group(3)
        comision_str = m2.group(4)
        moneda = m2.group(5)

        try:
            fecha = _parsea_fecha(fecha_str)
        except ValueError:
            return None

        hora = _parsea_hora(hora_str)

        try:
            monto_abs = _parsea_decimal(monto_str)
            comision = _parsea_decimal(comision_str)
        except ValueError:
            return None

        tipo, descripcion = _normaliza_descripcion(descripcion_raw)

        if tipo == "cargo":
            monto = -monto_abs
        elif tipo == "abono":
            monto = monto_abs
        else:
            cargos_por_naturaleza = {
                "Transferencia enviada",
                "Cobro automatico por deuda",
                "Dinero retenido",
            }
            monto = -monto_abs if descripcion in cargos_por_naturaleza else monto_abs

        if comision > 0:
            comision = -comision

        return Movimiento(
            fecha=fecha,
            hora=hora,
            descripcion=descripcion,
            identificador_transaccion=id_transaccion,
            monto=monto,
            comision=comision,
            moneda=moneda,
            confianza=NivelConfianza.ALTA,
        )

    def _es_linea_legacy(self, linea: str) -> bool:
        return _RE_LEGACY.match(linea) is not None

    def _intenta_parsear_legacy(self, linea: str) -> Optional[Movimiento]:
        match_fecha = re.match(r"^(\d{2}/\d{2}/\d{4})\s+", linea)
        if not match_fecha:
            return None

        fecha_str = match_fecha.group(1)
        resto = linea[match_fecha.end():]

        hora_str: Optional[str] = None
        match_hora = re.match(r"^(\d{2}:\d{2}:\d{2})\s+", resto)
        if match_hora:
            hora_str = match_hora.group(1)
            resto = resto[match_hora.end():]

        match_cola = re.search(
            r"\s+(\d+)\s+(-?[\d,]+\.\d{2})\s+(-?[\d,]+\.\d{2})\s+([A-Z]{3})\s*$",
            resto,
        )
        if not match_cola:
            return None

        descripcion_raw = resto[: match_cola.start()].strip()
        id_transaccion = match_cola.group(1)
        monto_str = match_cola.group(2)
        comision_str = match_cola.group(3)
        moneda = match_cola.group(4)

        try:
            fecha = _parsea_fecha(fecha_str)
        except ValueError:
            return None

        hora = _parsea_hora(hora_str) if hora_str else None

        try:
            monto_abs = _parsea_decimal(monto_str)
            comision = _parsea_decimal(comision_str)
        except ValueError:
            return None

        tipo, descripcion = _normaliza_descripcion(descripcion_raw)

        if tipo == "cargo":
            monto = -monto_abs
        elif tipo == "abono":
            monto = monto_abs
        else:
            cargos_por_naturaleza = {
                "Transferencia enviada",
                "Cobro automatico por deuda",
                "Dinero retenido",
            }
            monto = -monto_abs if descripcion in cargos_por_naturaleza else monto_abs

        if comision > 0:
            comision = -comision

        return Movimiento(
            fecha=fecha,
            hora=hora,
            descripcion=descripcion,
            identificador_transaccion=id_transaccion,
            monto=monto,
            comision=comision,
            moneda=moneda,
            confianza=NivelConfianza.ALTA,
        )

    def _extrae_spei(self, linea: str) -> Optional[dict]:
        resultado = {}

        match = _RE_SPEI_CLAVE.search(linea)
        if match:
            resultado["clave_rastreo"] = match.group(1)

        match = _RE_SPEI_CLABE.search(linea)
        if match:
            resultado["clabe"] = match.group(1)

        match = _RE_SPEI_BENEFICIARIO.search(linea)
        if match:
            resultado["beneficiario"] = _enmascara_nombre(match.group(1))

        return resultado if resultado else None

    def _detecta_espejos(self, extracto: ExtractoBancario) -> None:
        por_id: dict[str, list[int]] = defaultdict(list)
        for idx, mov in enumerate(extracto.movimientos):
            if mov.identificador_transaccion == "0":
                continue
            por_id[mov.identificador_transaccion].append(idx)

        pares: list[tuple[int, int]] = []

        for id_tx, indices in por_id.items():
            if len(indices) < 2:
                continue

            usados: set[int] = set()
            for i_pos, idx_a in enumerate(indices):
                if idx_a in usados:
                    continue
                mov_a = extracto.movimientos[idx_a]

                for idx_b in indices[i_pos + 1:]:
                    if idx_b in usados:
                        continue
                    mov_b = extracto.movimientos[idx_b]

                    if mov_a.monto + mov_b.monto == Decimal("0"):
                        pares.append((idx_a, idx_b))
                        extracto.movimientos[idx_a].es_espejo = True
                        extracto.movimientos[idx_b].es_espejo = True
                        usados.add(idx_a)
                        usados.add(idx_b)
                        break

        extracto.pares_espejo = pares

        if pares:
            total_espejo = sum(
                abs(extracto.movimientos[a].monto) for a, _ in pares
            )
            extracto.alertas.append(
                f"Se detectaron {len(pares)} pares de movimientos espejo "
                f"por un total de ${total_espejo:,.2f}. Estos movimientos "
                f"son internos y no representan ingreso ni gasto real."
            )

    def _valida_totales(self, extracto: ExtractoBancario) -> None:
        suma_abonos = sum(
            m.monto for m in extracto.movimientos if m.monto > 0
        )
        suma_cargos = sum(
            abs(m.monto) for m in extracto.movimientos if m.monto < 0
        )

        if suma_abonos != extracto.total_abonos_declarado:
            extracto.es_confiable = False
            extracto.alertas.append(
                f"Suma de abonos parseados (${suma_abonos:,.2f}) no coincide "
                f"con el total declarado (${extracto.total_abonos_declarado:,.2f}). "
                f"Diferencia: ${suma_abonos - extracto.total_abonos_declarado:,.2f}"
            )

        if suma_cargos != extracto.total_cargos_declarado:
            extracto.es_confiable = False
            extracto.alertas.append(
                f"Suma de cargos parseados (${suma_cargos:,.2f}) no coincide "
                f"con el total declarado (${extracto.total_cargos_declarado:,.2f}). "
                f"Diferencia: ${suma_cargos - extracto.total_cargos_declarado:,.2f}"
            )

    def _valida_comisiones(self, extracto: ExtractoBancario) -> None:
        suma_comisiones = sum(
            abs(m.comision) for m in extracto.movimientos
        )

        if suma_comisiones != extracto.comisiones_declaradas:
            extracto.alertas.append(
                f"Contradiccion en comisiones: los movimientos suman "
                f"${suma_comisiones:,.2f} en comisiones pero el encabezado "
                f"declara ${extracto.comisiones_declaradas:,.2f}. "
                f"Se marca el campo comision de cada movimiento como NO_CONFIABLE."
            )
            for mov in extracto.movimientos:
                if mov.comision != Decimal("0"):
                    mov.confianza = NivelConfianza.NO_CONFIABLE

    def _clasifica_movimientos(self, extracto: ExtractoBancario) -> None:
        for mov in extracto.movimientos:
            if "dinero retenido" in mov.descripcion.lower():
                mov.categoria = CATEGORIA_RETENCION

    def _verifica_descripciones(self, extracto: ExtractoBancario) -> None:
        descripciones_vistas: set[str] = set()

        for mov in extracto.movimientos:
            desc = mov.descripcion
            if desc not in DESCRIPCIONES_CONOCIDAS and desc not in descripciones_vistas:
                descripciones_vistas.add(desc)
                extracto.alertas.append(
                    f"Descripcion no reconocida: '{desc}'. "
                    f"Requiere revision manual para clasificacion fiscal."
                )


def parsea_texto_mercado_pago(texto: str) -> ExtractoBancario:
    """Parsea texto ya extraido (no PDF) de un estado de cuenta Mercado Pago.

    Soporta tanto formato real (dos lineas) como legacy (una linea).
    """
    adapter = MercadoPagoAdapter()
    return adapter._parsea_texto(texto)
