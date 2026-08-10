"""Adaptador completo para estados de cuenta de Mercado Pago Mexico.

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
from dataclasses import field
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

# Variantes con tilde que pueden aparecer en el PDF
_VARIANTES_TILDE: dict[str, str] = {
    "cobro automático por deuda": "Cobro automatico por deuda",
    "devolución de dinero": "Devolucion de dinero",
    "cancelación de transferencia recibida": "Cancelacion de transferencia recibida",
}

# Prefijos de tipo de movimiento
_PREFIJOS_TIPO = ("Abono - ", "Cargo - ")

# Categorias especiales
CATEGORIA_RETENCION = "retencion_temporal"
CATEGORIA_COMISION = "comision"

# ---------------------------------------------------------------------------
# Patrones regex para parseo
# ---------------------------------------------------------------------------

# Patron para lineas de movimiento:
# fecha  hora  descripcion  id_transaccion  monto  comision  moneda
_RE_MOVIMIENTO = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+"       # fecha DD/MM/YYYY
    r"(\d{2}:\d{2}:\d{2})?\s*"       # hora HH:MM:SS (opcional)
    r"(.+?)\s+"                       # descripcion
    r"(\d+)\s+"                       # identificador transaccion
    r"(-?[\d.,]+)\s+"                 # monto
    r"(-?[\d.,]+)\s+"                 # comision
    r"([A-Z]{3})\s*$"                 # moneda (3 letras)
)

# Patron alternativo: monto y comision pueden usar $ y parentesis
_RE_MONTO = re.compile(r"^\$?\s*-?([\d,]+\.\d{2})$")

# Patron para detectar SPEI
_RE_SPEI_CLAVE = re.compile(r"Clave de rastreo[:\s]+(\S+)", re.IGNORECASE)
_RE_SPEI_CLABE = re.compile(r"CLABE[:\s]+(\d{18})", re.IGNORECASE)
_RE_SPEI_BENEFICIARIO = re.compile(
    r"(?:Beneficiario|Ordenante)[:\s]+(.+)", re.IGNORECASE
)

# Patron para encabezado de totales
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
_RE_CUENTA = re.compile(
    r"(?:CVU|Cuenta|CLABE)[:\s]+(\d+)", re.IGNORECASE
)


def _parsea_decimal(texto: str) -> Decimal:
    """Convierte texto con formato mexicano a Decimal.

    Acepta formatos como: "1,234.56", "1234.56", "$1,234.56", "-1,234.56".
    """
    limpio = texto.strip().replace("$", "").replace(",", "").replace(" ", "")
    try:
        return Decimal(limpio)
    except InvalidOperation:
        raise ValueError(f"No se puede convertir a Decimal: {texto!r}")


def _parsea_fecha(texto: str) -> date:
    """Parsea fecha en formato DD/MM/YYYY."""
    partes = texto.strip().split("/")
    if len(partes) != 3:
        raise ValueError(f"Formato de fecha invalido: {texto!r}")
    dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
    return date(anio, mes, dia)


def _parsea_hora(texto: str) -> Optional[time]:
    """Parsea hora en formato HH:MM:SS. Retorna None si esta vacia."""
    if not texto or not texto.strip():
        return None
    partes = texto.strip().split(":")
    if len(partes) != 3:
        return None
    return time(int(partes[0]), int(partes[1]), int(partes[2]))


def _enmascara_nombre(nombre: str) -> str:
    """Enmascara un nombre dejando solo iniciales.

    'JUAN CARLOS PEREZ LOPEZ' -> 'J*** C*** P*** L***'
    """
    if not nombre or not nombre.strip():
        return "***"
    palabras = nombre.strip().split()
    return " ".join(p[0] + "***" for p in palabras if p)


def _enmascara_cuenta(cuenta: str) -> str:
    """Enmascara un numero de cuenta o CLABE dejando los ultimos 4 digitos.

    '1234567890123456' -> '************3456'
    """
    if not cuenta or len(cuenta) < 4:
        return "****"
    return "*" * (len(cuenta) - 4) + cuenta[-4:]


def _normaliza_descripcion(descripcion: str) -> tuple[str, str]:
    """Extrae el tipo (Abono/Cargo) y normaliza la descripcion.

    Returns:
        Tupla de (tipo_movimiento, descripcion_normalizada).
        tipo_movimiento es "abono" o "cargo".
    """
    texto = descripcion.strip()
    tipo = "otro"

    for prefijo in _PREFIJOS_TIPO:
        if texto.startswith(prefijo):
            tipo = "abono" if "Abono" in prefijo else "cargo"
            texto = texto[len(prefijo):]
            break

    # Normalizar variantes con tilde
    texto_lower = texto.lower().strip()
    if texto_lower in _VARIANTES_TILDE:
        texto = _VARIANTES_TILDE[texto_lower]

    # Capitalizar primera letra si no coincide exactamente
    for conocida in DESCRIPCIONES_CONOCIDAS:
        if texto.lower() == conocida.lower():
            texto = conocida
            break

    return tipo, texto


class MercadoPagoAdapter:
    """Adaptador completo para estados de cuenta de Mercado Pago Mexico.

    Implementa parseo de PDF, deteccion de espejos, validacion de totales,
    y clasificacion de movimientos.
    """

    institucion: str = "Mercado Pago"

    def detecta(self, texto: str) -> bool:
        """Retorna True si el texto corresponde a un estado de Mercado Pago.

        Busca marcadores especificos de Mercado Pago en el texto extraido.
        """
        texto_lower = texto.lower()
        marcadores = [
            "mercado pago",
            "mercadopago",
            "mercado libre",
        ]
        # Al menos uno de los marcadores principales
        tiene_marcador = any(m in texto_lower for m in marcadores)
        # Y algun indicio de estado de cuenta
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
        """Parsea un PDF de estado de cuenta de Mercado Pago.

        Proceso:
        1. Extrae texto del PDF con pdfplumber
        2. Parsea el encabezado para obtener totales declarados
        3. Parsea cada movimiento
        4. Detecta pares espejo
        5. Valida sumas contra totales declarados
        6. Marca comisiones como NO_CONFIABLE
        7. Clasifica movimientos especiales

        Args:
            path: Ruta al archivo PDF.

        Returns:
            ExtractoBancario con todos los datos y validaciones.
        """
        texto_completo = self._extrae_texto(path)
        lineas = texto_completo.split("\n")

        # 1. Parsear encabezado
        encabezado = self._parsea_encabezado(texto_completo)

        # 2. Parsear movimientos
        movimientos = self._parsea_movimientos(lineas)

        # 3. Crear extracto inicial
        alertas: list[str] = []

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
            alertas=alertas,
        )

        # 4. Detectar pares espejo
        self._detecta_espejos(extracto)

        # 5. Validar totales
        self._valida_totales(extracto)

        # 6. Validar comisiones
        self._valida_comisiones(extracto)

        # 7. Clasificar movimientos especiales
        self._clasifica_movimientos(extracto)

        # 8. Verificar descripciones conocidas
        self._verifica_descripciones(extracto)

        return extracto

    def _extrae_texto(self, path: Path) -> str:
        """Extrae texto del PDF usando pdfplumber."""
        with pdfplumber.open(path) as pdf:
            paginas = []
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    paginas.append(texto)
        return "\n".join(paginas)

    def _parsea_encabezado(self, texto: str) -> dict:
        """Extrae totales declarados del encabezado del estado de cuenta.

        El encabezado de Mercado Pago usa dos lineas de etiquetas seguidas
        de dos lineas de valores, parseados posicionalmente.
        """
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

        # Titular
        match = _RE_TITULAR.search(texto)
        if match:
            resultado["titular"] = _enmascara_nombre(match.group(1))

        # Cuenta / CVU
        match = _RE_CUENTA.search(texto)
        if match:
            resultado["cuenta"] = _enmascara_cuenta(match.group(1))

        # Periodo
        match = _RE_PERIODO.search(texto)
        if match:
            resultado["periodo_inicio"] = _parsea_fecha(match.group(1))
            resultado["periodo_fin"] = _parsea_fecha(match.group(2))

        # Saldo inicial
        match = _RE_SALDO_INICIAL.search(texto)
        if match:
            resultado["saldo_inicial"] = _parsea_decimal(match.group(1))

        # Saldo final
        match = _RE_SALDO_FINAL.search(texto)
        if match:
            resultado["saldo_final"] = _parsea_decimal(match.group(1))

        # Total de abonos
        match = _RE_TOTAL_ABONOS.search(texto)
        if match:
            resultado["total_abonos"] = _parsea_decimal(match.group(1))

        # Total de cargos
        match = _RE_TOTAL_CARGOS.search(texto)
        if match:
            resultado["total_cargos"] = _parsea_decimal(match.group(1))

        # Comisiones
        match = _RE_COMISIONES.search(texto)
        if match:
            resultado["comisiones"] = _parsea_decimal(match.group(1))

        return resultado

    def _parsea_movimientos(self, lineas: list[str]) -> list[Movimiento]:
        """Parsea las lineas de movimientos del estado de cuenta.

        Cada movimiento puede ocupar 1-3 lineas:
        - Linea principal: fecha, hora, descripcion, ID, monto, comision, moneda
        - Lineas adicionales opcionales: detalles SPEI
        """
        movimientos: list[Movimiento] = []
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            mov = self._intenta_parsear_linea_movimiento(linea)
            if mov is not None:
                # Buscar detalles SPEI en lineas siguientes
                detalle = {}
                j = i + 1
                while j < len(lineas) and j <= i + 5:
                    linea_detalle = lineas[j].strip()
                    # Si la siguiente linea es otro movimiento, parar
                    if self._intenta_parsear_linea_movimiento(linea_detalle) is not None:
                        break
                    # Buscar info SPEI
                    spei = self._extrae_spei(linea_detalle)
                    if spei:
                        detalle.update(spei)
                        j += 1
                    else:
                        break

                if detalle:
                    # Enmascarar CLABE en detalle
                    if "clabe" in detalle:
                        detalle["clabe"] = _enmascara_cuenta(detalle["clabe"])
                    mov.detalle = detalle

                movimientos.append(mov)
                i = j if detalle else i + 1
            else:
                i += 1

        return movimientos

    def _intenta_parsear_linea_movimiento(
        self, linea: str
    ) -> Optional[Movimiento]:
        """Intenta parsear una linea como movimiento.

        Formato esperado:
        DD/MM/YYYY  HH:MM:SS  Tipo - Descripcion  ID_transaccion  monto  comision  moneda

        Returns:
            Movimiento si la linea es valida, None si no.
        """
        # Formato flexible: fecha [hora] descripcion id monto comision moneda
        # La descripcion puede contener espacios, asi que parseamos desde los extremos

        # Verificar que empieza con fecha
        match_fecha = re.match(r"^(\d{2}/\d{2}/\d{4})\s+", linea)
        if not match_fecha:
            return None

        fecha_str = match_fecha.group(1)
        resto = linea[match_fecha.end():]

        # Intentar extraer hora
        hora_str: Optional[str] = None
        match_hora = re.match(r"^(\d{2}:\d{2}:\d{2})\s+", resto)
        if match_hora:
            hora_str = match_hora.group(1)
            resto = resto[match_hora.end():]

        # Desde el final: moneda (3 letras), comision, monto, ID
        # Patron: ... ID  monto  comision  MONEDA
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

        # Parsear valores
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

        # Determinar signo del monto segun tipo
        tipo, descripcion = _normaliza_descripcion(descripcion_raw)

        if tipo == "cargo":
            monto = -monto_abs
        elif tipo == "abono":
            monto = monto_abs
        else:
            # Si no tiene prefijo, intentar inferir del contexto
            # Descripciones que son cargos por naturaleza
            cargos_por_naturaleza = {
                "Transferencia enviada",
                "Cobro automatico por deuda",
                "Dinero retenido",
            }
            if descripcion in cargos_por_naturaleza:
                monto = -monto_abs
            else:
                monto = monto_abs

        # Asegurar que la comision sea negativa (es un cargo)
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
        """Extrae informacion SPEI de una linea de detalle."""
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
        """Detecta pares de movimientos espejo.

        Un par espejo son dos movimientos con:
        - El mismo identificador de transaccion (distinto de "0")
        - Montos exactamente opuestos (uno positivo, uno negativo)

        Estos representan movimientos internos de Mercado Pago y NO deben
        contarse como ingreso ni como gasto.
        """
        # Agrupar por ID de transaccion
        por_id: dict[str, list[int]] = defaultdict(list)
        for idx, mov in enumerate(extracto.movimientos):
            # ID "0" es generico, no emparejar
            if mov.identificador_transaccion == "0":
                continue
            por_id[mov.identificador_transaccion].append(idx)

        pares: list[tuple[int, int]] = []

        for id_tx, indices in por_id.items():
            if len(indices) < 2:
                continue

            # Buscar pares con montos opuestos
            usados: set[int] = set()
            for i_pos, idx_a in enumerate(indices):
                if idx_a in usados:
                    continue
                mov_a = extracto.movimientos[idx_a]

                for idx_b in indices[i_pos + 1 :]:
                    if idx_b in usados:
                        continue
                    mov_b = extracto.movimientos[idx_b]

                    # Verificar montos exactamente opuestos
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
        """Valida que la suma de movimientos parseados coincida con los
        totales declarados en el encabezado.

        IMPORTANTE: En Mercado Pago la formula de saldo (inicial + abonos -
        cargos = final) generalmente NO cuadra. El invariante correcto es
        que la suma de movimientos parseados coincida al centavo con los
        totales de abonos y cargos declarados.
        """
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
        """Valida comisiones y marca como NO_CONFIABLE si hay contradiccion.

        En Mercado Pago las comisiones en los movimientos frecuentemente
        contradicen el total declarado en el encabezado.
        """
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
            # Marcar cada movimiento con comision
            for mov in extracto.movimientos:
                if mov.comision != Decimal("0"):
                    mov.confianza = NivelConfianza.NO_CONFIABLE

    def _clasifica_movimientos(self, extracto: ExtractoBancario) -> None:
        """Clasifica movimientos con categorias especiales.

        - 'Dinero retenido': retencion temporal de fondos, no gasto real
        """
        for mov in extracto.movimientos:
            desc_lower = mov.descripcion.lower()
            if "dinero retenido" in desc_lower:
                mov.categoria = CATEGORIA_RETENCION

    def _verifica_descripciones(self, extracto: ExtractoBancario) -> None:
        """Verifica que todas las descripciones sean conocidas.

        Las descripciones no reconocidas generan una alerta para revision
        manual en lugar de fallar silenciosamente.
        """
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

    Util para testing con fixtures de texto plano.

    Args:
        texto: Texto completo del estado de cuenta.

    Returns:
        ExtractoBancario parseado.
    """
    adapter = MercadoPagoAdapter()
    lineas = texto.split("\n")

    encabezado = adapter._parsea_encabezado(texto)

    movimientos = adapter._parsea_movimientos(lineas)

    alertas: list[str] = []

    extracto = ExtractoBancario(
        institucion=adapter.institucion,
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
        alertas=alertas,
    )

    adapter._detecta_espejos(extracto)
    adapter._valida_totales(extracto)
    adapter._valida_comisiones(extracto)
    adapter._clasifica_movimientos(extracto)
    adapter._verifica_descripciones(extracto)

    return extracto
