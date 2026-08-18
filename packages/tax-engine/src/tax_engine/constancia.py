"""
Extraccion de datos de Constancia de Situacion Fiscal (SAT).

La constancia es un PDF emitido por el SAT que contiene:
- RFC del contribuyente
- Nombre o razon social
- Tipo de persona (fisica o moral)
- Regimen(es) fiscal(es) activos
- Obligaciones fiscales
- Domicilio fiscal

El regimen se extrae de la constancia, nunca se pide al usuario.

Implementacion:
- pdfplumber para extraer tablas y texto del PDF.
- Descripciones de regimen se mapean a claves SAT via catalogo c_RegimenFiscal.
- Periodicidad de obligaciones se deriva del texto de vencimiento.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from tax_engine.rfc import validar_rfc


@dataclass
class RegimenConstancia:
    """Regimen fiscal tal como aparece en la constancia."""
    clave_sat: str
    descripcion: str
    fecha_alta: str
    vigente: bool = True


@dataclass
class ObligacionConstancia:
    """Obligacion fiscal listada en la constancia."""
    descripcion: str
    periodicidad: str
    fecha_inicio: str


@dataclass
class DatosConstancia:
    """Datos extraidos de la Constancia de Situacion Fiscal."""
    rfc: str
    nombre: str
    tipo_persona: str  # "fisica" | "moral"
    regimenes: list[RegimenConstancia] = field(default_factory=list)
    obligaciones: list[ObligacionConstancia] = field(default_factory=list)
    domicilio_cp: str = ""
    valido: bool = True
    error: str = ""
    regimenes_tabla_presente: bool = False


# --- Catalogo c_RegimenFiscal: descripcion normalizada -> clave SAT ---

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

# Mapa corregido contra catalogo c_RegimenFiscal oficial.
# Cada clave SAT mapea a su regimen interno correcto.
_MAPA_REGIMEN_SAT: dict[str, str] = {
    "601": "GENERAL_LEY_PM",
    "603": "PERSONAS_MORALES_SIN_FINES_LUCRO",
    "605": "SUELDOS_SALARIOS",
    "606": "ARRENDAMIENTO",
    "607": "ENAJENACION_ADQUISICION",
    "608": "DEMAS_INGRESOS",
    "610": "RESIDENTES_EXTRANJERO",
    "611": "DIVIDENDOS",
    "612": "ACTIVIDAD_EMPRESARIAL",
    "614": "INGRESOS_INTERESES",
    "615": "OBTENCION_PREMIOS",
    "616": "SIN_OBLIGACIONES",
    "620": "COOPERATIVAS_DIFERIMIENTO",
    "621": "INCORPORACION_FISCAL",
    "622": "ACTIVIDADES_AGRICOLAS",
    "623": "OPCIONAL_GRUPO_SOCIEDADES",
    "624": "COORDINADOS",
    "625": "PLATAFORMAS_TECNOLOGICAS",
    "626": "RESICO",  # Se resuelve a PF o PM segun longitud del RFC
    "628": "HIDROCARBUROS",
    "629": "REGIMENES_PREFERENTES",
    "630": "ENAJENACION_ACCIONES",
}


# --- Normalizacion de texto ---

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparacion: minusculas, sin acentos, sin puntuacion final, espacios colapsados."""
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.rstrip(".")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def descripcion_a_clave_sat(descripcion: str) -> str | None:
    """Mapea una descripcion de regimen del PDF a su clave SAT.

    Primero intenta coincidencia exacta con el catalogo normalizado.
    Si falla, intenta coincidencia por contencion para tolerar variaciones
    en el texto entre distintos anios del SAT.
    """
    norm = normalizar_texto(descripcion)
    clave = _CATALOGO_REGIMEN.get(norm)
    if clave:
        return clave

    for desc_catalogo, clave_cat in _CATALOGO_REGIMEN.items():
        if desc_catalogo in norm or norm in desc_catalogo:
            return clave_cat

    return None


# --- Periodicidad ---

_PATRON_MENSUAL = re.compile(r"\bmensu(?:al|almente)\b|\bmes\s*inmediato\b", re.IGNORECASE)
_PATRON_BIMESTRAL = re.compile(r"\bbimestr(?:al|almente)\b", re.IGNORECASE)
_PATRON_TRIMESTRAL = re.compile(r"\btrimestr(?:al|almente)\b", re.IGNORECASE)
_PATRON_ANUAL = re.compile(r"\banu(?:al|almente)\b", re.IGNORECASE)

def derivar_periodicidad(texto_vencimiento: str) -> str:
    """Deriva periodicidad del texto de 'Descripcion Vencimiento' de la constancia."""
    if _PATRON_MENSUAL.search(texto_vencimiento):
        return "mensual"
    if _PATRON_BIMESTRAL.search(texto_vencimiento):
        return "bimestral"
    if _PATRON_TRIMESTRAL.search(texto_vencimiento):
        return "trimestral"
    if _PATRON_ANUAL.search(texto_vencimiento):
        return "anual"
    return "desconocida"


# --- Parsing de fechas en espanol ---

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
    """Parsea '01 DE OCTUBRE DE 2020' -> '2020-10-01'. Si falla, devuelve el texto original."""
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


# --- Extraccion de bloque de identificacion ---
# Bug 2 fix: tolerar cero o mas espacios entre etiqueta y valor (\s* en vez de \s+)

_RE_RFC = re.compile(r"RFC\s*:?\s*([A-ZÑ&0-9]{12,13})", re.IGNORECASE)
_RE_CURP = re.compile(r"CURP\s*:?\s*([A-Z0-9]{18})", re.IGNORECASE)
_RE_NOMBRE = re.compile(
    r"(?:Nombre|Denominaci[oó]n|Raz[oó]n\s*Social)\s*(?:\([^)]*\))?\s*:?\s*(.+)",
    re.IGNORECASE,
)
_RE_ESTATUS = re.compile(r"Estatus\s*en\s*el\s*padr[oó]n\s*:?\s*(\w+)", re.IGNORECASE)
_RE_FECHA_INICIO = re.compile(
    r"Fecha\s*(?:de\s*)?inicio\s*(?:de\s*)?operaciones?\s*:?\s*(.+)",
    re.IGNORECASE,
)
_RE_CP = re.compile(r"C[oó]digo\s*Postal\s*:?\s*(\d{5})", re.IGNORECASE)


def _extraer_identificacion(texto: str) -> dict:
    """Extrae datos del bloque de identificacion del contribuyente."""
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


def _normalizar_para_etiqueta(texto: str) -> str:
    """Normaliza texto de etiqueta insertando espacios antes de mayusculas internas.

    El PDF del SAT a veces concatena palabras sin espacio (ej: 'PrimerApellido:').
    normalizar_texto() colapsa espacios pero no los inserta. Esta funcion
    agrega un espacio antes de cada mayuscula precedida de minuscula para
    separar palabras concatenadas, y luego aplica normalizar_texto().
    """
    separado = re.sub(r"(?<=[a-záéíóúüñ])(?=[A-ZÁÉÍÓÚÜÑ])", " ", texto)
    return normalizar_texto(separado)


def _extraer_nombre_de_tablas(tablas: list[list[list[str | None]]]) -> str | None:
    """Intenta armar el nombre completo concatenando celdas de tabla de identificacion.

    En PDFs reales del SAT, pdfplumber extrae una tabla de identificacion con filas
    como ['Nombre (s):', 'JUAN'], ['Primer Apellido:', 'PEREZ'], etc.
    Las concatenamos para obtener el nombre completo.
    """
    nombre_partes: dict[str, str] = {}
    for tabla in tablas:
        for fila in tabla:
            if not fila or len(fila) < 2:
                continue
            etiqueta = _normalizar_para_etiqueta(fila[0] or "")
            valor = (fila[1] or "").strip()
            if not valor:
                continue
            if "nombre" in etiqueta and "comercial" not in etiqueta and "vialidad" not in etiqueta and "colonia" not in etiqueta and "localidad" not in etiqueta and "municipio" not in etiqueta and "entidad" not in etiqueta:
                if "primer" not in etiqueta and "segundo" not in etiqueta:
                    nombre_partes["nombre"] = valor
            if "primer apellido" in etiqueta:
                nombre_partes["primer_apellido"] = valor
            if "segundo apellido" in etiqueta:
                nombre_partes["segundo_apellido"] = valor
            if "denominacion" in etiqueta or "razon social" in etiqueta:
                nombre_partes["razon_social"] = valor

    if "razon_social" in nombre_partes:
        return nombre_partes["razon_social"]

    partes = []
    for k in ("nombre", "primer_apellido", "segundo_apellido"):
        v = nombre_partes.get(k)
        if v:
            partes.append(v)
    return " ".join(partes) if partes else None


# --- Deteccion de encabezado real en tablas ---

def _buscar_encabezado(
    tabla: list[list[str | None]],
    palabras_requeridas: list[list[str]],
) -> int:
    """Busca la primera fila que contenga las palabras clave esperadas.

    Args:
        tabla: Tabla extraida por pdfplumber.
        palabras_requeridas: Lista de grupos de palabras clave. Cada grupo es
            una lista de alternativas; se requiere que al menos un grupo
            tenga coincidencia Y que al menos dos celdas no esten vacias.

    Returns:
        Indice de la fila del encabezado, o -1 si no se encuentra.
    """
    for i, fila in enumerate(tabla):
        celdas_no_vacias = [c for c in fila if (c or "").strip()]
        if len(celdas_no_vacias) < 2:
            continue

        texto_fila = " ".join(normalizar_texto(c or "") for c in fila)
        grupos_encontrados = 0
        for grupo in palabras_requeridas:
            if any(palabra in texto_fila for palabra in grupo):
                grupos_encontrados += 1
        if grupos_encontrados >= len(palabras_requeridas):
            return i
    return -1


# --- Extraccion principal via pdfplumber ---

def _extraer_regimenes_de_tablas(tablas: list[list[list[str | None]]]) -> tuple[list[RegimenConstancia], bool]:
    """Busca la tabla de regimenes en las tablas extraidas por pdfplumber.

    Returns:
        Tupla de (lista de regimenes, si se encontro la tabla de regimenes).
    """
    regimenes: list[RegimenConstancia] = []
    tabla_encontrada = False

    for tabla in tablas:
        if not tabla or len(tabla) < 2:
            continue

        idx_encabezado = _buscar_encabezado(tabla, [
            ["regimen"],
            ["fecha"],
        ])
        if idx_encabezado == -1:
            continue

        tabla_encontrada = True
        encabezado = [normalizar_texto(c or "") for c in tabla[idx_encabezado]]

        idx_desc = -1
        idx_fecha = -1
        for i, h in enumerate(encabezado):
            if "regimen" in h or "descripcion" in h:
                idx_desc = i
            if "fecha" in h and "fin" not in h and idx_fecha == -1:
                idx_fecha = i

        if idx_desc == -1:
            continue

        for fila in tabla[idx_encabezado + 1:]:
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

    return regimenes, tabla_encontrada


def _extraer_obligaciones_de_tablas(tablas: list[list[list[str | None]]]) -> list[ObligacionConstancia]:
    """Busca la tabla de obligaciones en las tablas extraidas por pdfplumber."""
    obligaciones: list[ObligacionConstancia] = []
    for tabla in tablas:
        if not tabla or len(tabla) < 2:
            continue

        idx_encabezado = _buscar_encabezado(tabla, [
            ["obligacion"],
            ["vencimiento"],
        ])
        if idx_encabezado == -1:
            continue

        encabezado = [normalizar_texto(c or "") for c in tabla[idx_encabezado]]

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

        for fila in tabla[idx_encabezado + 1:]:
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

    Usa pdfplumber para extraer tablas y texto. Delega la logica
    de parsing a funciones especializadas.
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
    Extrae datos de la constancia a partir del texto ya extraido del PDF.

    Para PDFs completos, usar `extraer_constancia_desde_pdf()` que extrae
    tablas con pdfplumber. Esta funcion opera solo sobre texto plano,
    util para tests y cuando la extraccion de texto se hace externamente.
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
    """Logica central de parsing compartida entre ambas entradas."""
    ident = _extraer_identificacion(texto)

    rfc = ident.get("rfc", "")
    nombre = ident.get("nombre", "")
    cp = ident.get("domicilio_cp", "")

    if tablas:
        nombre_tablas = _extraer_nombre_de_tablas(tablas)
        if nombre_tablas:
            nombre = nombre_tablas

    tipo_persona = ""
    if rfc:
        resultado_rfc = validar_rfc(rfc)
        tipo_persona = resultado_rfc.tipo_persona

    regimenes: list[RegimenConstancia] = []
    regimenes_tabla_presente = False
    obligaciones: list[ObligacionConstancia] = []

    if tablas:
        regimenes, regimenes_tabla_presente = _extraer_regimenes_de_tablas(tablas)
        obligaciones = _extraer_obligaciones_de_tablas(tablas)

    if not rfc and not regimenes:
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False,
            error="No se pudo extraer RFC ni regímenes de la constancia",
        )

    valido = True
    error = ""
    if rfc and regimenes_tabla_presente and not regimenes:
        valido = False
        error = "Constancia tiene tabla de regímenes pero no se pudo extraer ninguno"

    return DatosConstancia(
        rfc=rfc,
        nombre=nombre,
        tipo_persona=tipo_persona,
        regimenes=regimenes,
        obligaciones=obligaciones,
        domicilio_cp=cp,
        valido=valido,
        error=error,
        regimenes_tabla_presente=regimenes_tabla_presente,
    )


def mapear_regimen_sat(clave: str, rfc: str = "") -> str | None:
    """
    Traduce clave de regimen SAT al enum del sistema.

    Solo devuelve un valor para regimenes que el motor soporta activamente.
    Para 626 (RESICO), distingue PF vs PM segun longitud del RFC.
    Para 625 (Plataformas Tecnologicas), devuelve "PLATAFORMAS_TECNOLOGICAS"
    como senal para enviar a lista de espera.
    """
    interno = _MAPA_REGIMEN_SAT.get(clave)
    if interno is None:
        return None

    if clave == "626":
        if len(rfc) == 13:
            return "RESICO_PF"
        elif len(rfc) == 12:
            return "RESICO_PM"
        return "RESICO_PF"

    if interno in ("RESICO_PF", "ARRENDAMIENTO"):
        return interno

    if interno == "PLATAFORMAS_TECNOLOGICAS":
        return "PLATAFORMAS_TECNOLOGICAS"

    if interno == "SUELDOS_SALARIOS":
        return "SUELDOS_SALARIOS"

    return None


def derivar_regimen_de_constancia(datos: DatosConstancia) -> str | None:
    """
    Determina el regimen del sistema a partir de los regimenes en la constancia.

    Si la constancia lista un solo regimen soportado, lo devuelve.
    Si lista multiples regimenes soportados, aplica reglas de prioridad.
    Si no lista ningun regimen soportado, devuelve None.

    Retorna "PLATAFORMAS_TECNOLOGICAS" para clave 625 — el caller debe
    enviar a lista de espera en vez de continuar al motor de calculo.
    Retorna variantes con _SUELDOS si tambien tiene clave 605.
    """
    if not datos.regimenes:
        return None

    rfc = datos.rfc or ""
    soportados: list[str] = []
    tiene_sueldos = False

    for reg in datos.regimenes:
        if not reg.vigente:
            continue
        if reg.clave_sat == "605":
            tiene_sueldos = True
            continue
        interno = mapear_regimen_sat(reg.clave_sat, rfc)
        if interno:
            soportados.append(interno)

    if not soportados:
        return None

    if "PLATAFORMAS_TECNOLOGICAS" in soportados:
        return "PLATAFORMAS_TECNOLOGICAS"

    if len(soportados) == 1:
        regimen = soportados[0]
    elif "ARRENDAMIENTO" in soportados and "RESICO_PF" in soportados:
        regimen = "ARRENDAMIENTO"
    else:
        regimen = soportados[0]

    if tiene_sueldos and regimen in ("RESICO_PF", "ARRENDAMIENTO"):
        regimen = f"{regimen}_SUELDOS"

    return regimen
