"""
Extracción de datos de Constancia de Situación Fiscal (SAT).

La constancia es un PDF emitido por el SAT que contiene:
- RFC del contribuyente
- Nombre o razón social
- Tipo de persona (física o moral)
- Régimen(es) fiscal(es) activos
- Obligaciones fiscales
- Domicilio fiscal

El régimen se extrae de la constancia, nunca se pide al usuario.

Implementación:
- pdfplumber para extraer tablas y texto del PDF.
- Descripciones de régimen se mapean a claves SAT vía catálogo c_RegimenFiscal.
- Periodicidad de obligaciones se deriva del texto de vencimiento.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from tax_engine.rfc import validar_rfc


@dataclass
class RegimenConstancia:
    """Régimen fiscal tal como aparece en la constancia."""
    clave_sat: str
    descripcion: str
    fecha_alta: str
    vigente: bool = True


@dataclass
class ObligacionConstancia:
    """Obligación fiscal listada en la constancia."""
    descripcion: str
    periodicidad: str
    fecha_inicio: str


@dataclass
class DatosConstancia:
    """Datos extraídos de la Constancia de Situación Fiscal."""
    rfc: str
    nombre: str
    tipo_persona: str  # "fisica" | "moral"
    regimenes: list[RegimenConstancia] = field(default_factory=list)
    obligaciones: list[ObligacionConstancia] = field(default_factory=list)
    domicilio_cp: str = ""
    valido: bool = True
    error: str = ""


# --- Catálogo c_RegimenFiscal: descripción normalizada → clave SAT ---

_CATALOGO_REGIMEN: dict[str, str] = {
    "general de ley personas morales": "601",
    "personas morales con fines no lucrativos": "603",
    "sueldos y salarios e ingresos asimilados a salarios": "605",
    "arrendamiento": "606",
    "regimen de enajenacion o adquisicion de bienes": "607",
    "demas ingresos": "608",
    "residentes en el extranjero sin establecimiento permanente en mexico": "610",
    "ingresos por dividendos (socios y accionistas)": "611",
    "personas fisicas con actividades empresariales y profesionales": "612",
    "ingresos por intereses": "614",
    "regimen de los ingresos por obtencion de premios": "615",
    "sin obligaciones fiscales": "616",
    "sociedades cooperativas de produccion que optan por diferir sus ingresos": "620",
    "incorporacion fiscal": "621",
    "actividades agricolas, ganaderas, silvicolas y pesqueras": "622",
    "opcional para grupos de sociedades": "623",
    "coordinados": "624",
    "regimen de las actividades empresariales con ingresos a traves de plataformas tecnologicas": "625",
    "regimen simplificado de confianza": "626",
    "hidrocarburos": "628",
    "de los regimenes fiscales preferentes y de las empresas multinacionales": "629",
    "enajenacion de acciones en bolsa de valores": "630",
}

_MAPA_REGIMEN_SAT = {
    "612": "RESICO_PF",
    "606": "ARRENDAMIENTO",
    "625": "RESICO_PM",
    "601": "GENERAL_LEY_PM",
    "603": "AUTOTRANSPORTE",
    "605": "SUELDOS_SALARIOS",
    "610": "RESIDENTES_EXTRANJERO",
    "611": "DIVIDENDOS",
    "614": "AGRICOLA",
    "615": "ACTIVIDAD_EMPRESARIAL",
    "616": "SIN_OBLIGACIONES",
    "621": "INCORPORACION_FISCAL",
    "622": "ACTIVIDADES_AGRICOLAS",
    "623": "OPCIONAL_GRUPO_SOCIEDADES",
    "624": "COORDINADOS",
    "626": "SIMPLIFICADO_CONFIANZA_PM",
    "628": "HIDROCARBUROS",
    "629": "ENAJENACION_ADQUISICION",
    "630": "ENAJENACION_ACCIONES",
}


# --- Normalización de texto ---

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin puntuación final, espacios colapsados."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.rstrip(".")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def descripcion_a_clave_sat(descripcion: str) -> str | None:
    """Mapea una descripción de régimen del PDF a su clave SAT."""
    norm = normalizar_texto(descripcion)
    return _CATALOGO_REGIMEN.get(norm)


# --- Periodicidad ---

_PATRON_MENSUAL = re.compile(r"\bmensu(?:al|almente)\b|\bmes\s+inmediato\b", re.IGNORECASE)
_PATRON_BIMESTRAL = re.compile(r"\bbimestr(?:al|almente)\b", re.IGNORECASE)
_PATRON_TRIMESTRAL = re.compile(r"\btrimestr(?:al|almente)\b", re.IGNORECASE)
_PATRON_ANUAL = re.compile(r"\banu(?:al|almente)\b", re.IGNORECASE)

def derivar_periodicidad(texto_vencimiento: str) -> str:
    """Deriva periodicidad del texto de 'Descripción Vencimiento' de la constancia."""
    if _PATRON_MENSUAL.search(texto_vencimiento):
        return "mensual"
    if _PATRON_BIMESTRAL.search(texto_vencimiento):
        return "bimestral"
    if _PATRON_TRIMESTRAL.search(texto_vencimiento):
        return "trimestral"
    if _PATRON_ANUAL.search(texto_vencimiento):
        return "anual"
    return "desconocida"


# --- Parsing de fechas en español ---

_MESES_ES: dict[str, int] = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_RE_FECHA_LARGA = re.compile(
    r"(\d{1,2})\s+DE\s+(\w+)\s+DE\s+(\d{4})",
    re.IGNORECASE,
)

def parsear_fecha_espanol(texto: str) -> str:
    """Parsea '01 DE OCTUBRE DE 2020' → '2020-10-01'. Si falla, devuelve el texto original."""
    m = _RE_FECHA_LARGA.search(texto)
    if not m:
        return texto.strip()
    dia = int(m.group(1))
    mes_nombre = m.group(2).lower()
    anio = int(m.group(3))
    mes = _MESES_ES.get(mes_nombre)
    if mes is None:
        return texto.strip()
    return f"{anio:04d}-{mes:02d}-{dia:02d}"


# --- Extracción de bloque de identificación ---

_RE_RFC = re.compile(r"RFC\s*:\s*([A-ZÑ&0-9]{12,13})", re.IGNORECASE)
_RE_CURP = re.compile(r"CURP\s*:\s*([A-Z0-9]{18})", re.IGNORECASE)
_RE_NOMBRE = re.compile(r"(?:Nombre|Denominaci[oó]n|Raz[oó]n Social)\s*(?:\([^)]*\))?\s*:\s*(.+)", re.IGNORECASE)
_RE_ESTATUS = re.compile(r"Estatus\s+en\s+el\s+padr[oó]n\s*:\s*(\w+)", re.IGNORECASE)
_RE_FECHA_INICIO = re.compile(r"Fecha\s+de\s+inicio\s+de\s+operaciones?\s*:\s*(.+)", re.IGNORECASE)
_RE_CP = re.compile(r"C[oó]digo\s+Postal\s*:\s*(\d{5})", re.IGNORECASE)


def _extraer_identificacion(texto: str) -> dict:
    """Extrae datos del bloque de identificación del contribuyente."""
    datos: dict = {}

    m = _RE_RFC.search(texto)
    if m:
        datos["rfc"] = m.group(1).upper()

    m = _RE_CURP.search(texto)
    if m:
        datos["curp"] = m.group(1).upper()

    m = _RE_NOMBRE.search(texto)
    if m:
        datos["nombre"] = m.group(1).strip()

    m = _RE_ESTATUS.search(texto)
    if m:
        datos["estatus"] = m.group(1).strip()

    m = _RE_FECHA_INICIO.search(texto)
    if m:
        datos["fecha_inicio"] = parsear_fecha_espanol(m.group(1).strip())

    m = _RE_CP.search(texto)
    if m:
        datos["domicilio_cp"] = m.group(1)

    return datos


# --- Extracción principal vía pdfplumber ---

def _extraer_regimenes_de_tablas(tablas: list[list[list[str | None]]]) -> list[RegimenConstancia]:
    """Busca la tabla de regímenes en las tablas extraídas por pdfplumber."""
    regimenes: list[RegimenConstancia] = []
    for tabla in tablas:
        if not tabla or len(tabla) < 2:
            continue

        encabezado = [normalizar_texto(c or "") for c in tabla[0]]

        tiene_regimen = any("regimen" in h or "descripcion" in h for h in encabezado)
        tiene_fecha = any("fecha" in h for h in encabezado)
        if not tiene_regimen or not tiene_fecha:
            continue

        idx_desc = -1
        idx_fecha = -1
        for i, h in enumerate(encabezado):
            if "regimen" in h or "descripcion" in h:
                idx_desc = i
            if "fecha" in h and idx_fecha == -1:
                idx_fecha = i

        if idx_desc == -1:
            continue

        for fila in tabla[1:]:
            if len(fila) <= max(idx_desc, idx_fecha if idx_fecha >= 0 else 0):
                continue
            desc_raw = (fila[idx_desc] or "").strip()
            if not desc_raw:
                continue

            fecha_raw = (fila[idx_fecha] or "").strip() if idx_fecha >= 0 and idx_fecha < len(fila) else ""
            fecha = parsear_fecha_espanol(fecha_raw) if fecha_raw else ""

            clave = descripcion_a_clave_sat(desc_raw)
            regimenes.append(RegimenConstancia(
                clave_sat=clave or "",
                descripcion=desc_raw,
                fecha_alta=fecha,
                vigente=True,
            ))

    return regimenes


def _extraer_obligaciones_de_tablas(tablas: list[list[list[str | None]]]) -> list[ObligacionConstancia]:
    """Busca la tabla de obligaciones en las tablas extraídas por pdfplumber."""
    obligaciones: list[ObligacionConstancia] = []
    for tabla in tablas:
        if not tabla or len(tabla) < 2:
            continue

        encabezado = [normalizar_texto(c or "") for c in tabla[0]]

        tiene_obligacion = any("obligacion" in h or "descripcion de la obligacion" in h for h in encabezado)
        tiene_vencimiento = any("vencimiento" in h for h in encabezado)
        if not tiene_obligacion:
            continue

        idx_desc = -1
        idx_vencimiento = -1
        idx_fecha = -1
        for i, h in enumerate(encabezado):
            if "obligacion" in h or ("descripcion" in h and "vencimiento" not in h):
                idx_desc = i
            if "vencimiento" in h:
                idx_vencimiento = i
            if "fecha" in h and "inicio" in h:
                idx_fecha = i

        if idx_desc == -1:
            continue

        for fila in tabla[1:]:
            if len(fila) <= idx_desc:
                continue
            desc_raw = (fila[idx_desc] or "").strip()
            if not desc_raw:
                continue

            venc_raw = ""
            if idx_vencimiento >= 0 and idx_vencimiento < len(fila):
                venc_raw = (fila[idx_vencimiento] or "").strip()

            fecha_raw = ""
            if idx_fecha >= 0 and idx_fecha < len(fila):
                fecha_raw = (fila[idx_fecha] or "").strip()

            periodicidad = derivar_periodicidad(venc_raw) if venc_raw else "desconocida"
            fecha = parsear_fecha_espanol(fecha_raw) if fecha_raw else ""

            obligaciones.append(ObligacionConstancia(
                descripcion=desc_raw,
                periodicidad=periodicidad,
                fecha_inicio=fecha,
            ))

    return obligaciones


def extraer_constancia_desde_pdf(ruta_pdf: str | Path) -> DatosConstancia:
    """
    Extrae datos de la constancia a partir de un archivo PDF.

    Usa pdfplumber para extraer tablas y texto. Delega la lógica
    de parsing a funciones especializadas.

    Args:
        ruta_pdf: Ruta al archivo PDF de la constancia.

    Returns:
        DatosConstancia con los datos extraídos.
    """
    try:
        import pdfplumber
    except ImportError:
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False, error="pdfplumber no instalado",
        )

    ruta = Path(ruta_pdf)
    if not ruta.exists():
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False, error=f"Archivo no encontrado: {ruta}",
        )

    try:
        with pdfplumber.open(ruta) as pdf:
            texto_completo = ""
            todas_tablas: list[list[list[str | None]]] = []
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text() or ""
                texto_completo += texto_pagina + "\n"
                tablas_pagina = pagina.extract_tables() or []
                todas_tablas.extend(tablas_pagina)
    except Exception as e:
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False, error=f"Error leyendo PDF: {e}",
        )

    return _parsear_constancia(texto_completo, todas_tablas)


def extraer_constancia(texto_pdf: str) -> DatosConstancia:
    """
    Extrae datos de la constancia a partir del texto ya extraído del PDF.

    Para PDFs completos, usar `extraer_constancia_desde_pdf()` que extrae
    tablas con pdfplumber. Esta función opera solo sobre texto plano,
    útil para tests y cuando la extracción de texto se hace externamente.

    Args:
        texto_pdf: Texto completo extraído del PDF de la constancia.

    Returns:
        DatosConstancia con los datos extraídos.
    """
    if not texto_pdf or not texto_pdf.strip():
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False, error="Texto de constancia vacío",
        )

    return _parsear_constancia(texto_pdf, [])


def _parsear_constancia(
    texto: str,
    tablas: list[list[list[str | None]]],
) -> DatosConstancia:
    """Lógica central de parsing compartida entre ambas entradas."""
    ident = _extraer_identificacion(texto)

    rfc = ident.get("rfc", "")
    nombre = ident.get("nombre", "")
    cp = ident.get("domicilio_cp", "")

    tipo_persona = ""
    if rfc:
        resultado_rfc = validar_rfc(rfc)
        tipo_persona = resultado_rfc.tipo_persona

    regimenes = _extraer_regimenes_de_tablas(tablas) if tablas else []
    obligaciones = _extraer_obligaciones_de_tablas(tablas) if tablas else []

    if not rfc and not regimenes:
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False,
            error="No se pudo extraer RFC ni regímenes de la constancia",
        )

    return DatosConstancia(
        rfc=rfc,
        nombre=nombre,
        tipo_persona=tipo_persona,
        regimenes=regimenes,
        obligaciones=obligaciones,
        domicilio_cp=cp,
        valido=True,
    )


def mapear_regimen_sat(clave: str) -> str | None:
    """
    Traduce clave de régimen SAT al enum del sistema.

    Solo devuelve un valor para regímenes que el motor soporta.
    Para regímenes no soportados, devuelve None.
    """
    interno = _MAPA_REGIMEN_SAT.get(clave)
    if interno in ("RESICO_PF", "ARRENDAMIENTO"):
        return interno
    return None


def derivar_regimen_de_constancia(datos: DatosConstancia) -> str | None:
    """
    Determina el régimen del sistema a partir de los regímenes en la constancia.

    Si la constancia lista un solo régimen soportado, lo devuelve.
    Si lista múltiples regímenes soportados, aplica reglas de prioridad.
    Si no lista ningún régimen soportado, devuelve None.
    """
    if not datos.regimenes:
        return None

    soportados = []
    for reg in datos.regimenes:
        if not reg.vigente:
            continue
        interno = mapear_regimen_sat(reg.clave_sat)
        if interno:
            soportados.append(interno)

    if not soportados:
        return None

    if len(soportados) == 1:
        return soportados[0]

    if "ARRENDAMIENTO" in soportados and "RESICO_PF" in soportados:
        return "ARRENDAMIENTO"

    return soportados[0]
