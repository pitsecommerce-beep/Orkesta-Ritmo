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
"""

from dataclasses import dataclass, field

from tax_engine.rfc import validar_rfc, ResultadoRfc


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


def extraer_constancia(texto_pdf: str) -> DatosConstancia:
    """
    Extrae datos de la constancia a partir del texto del PDF.

    Esta función recibe el texto ya extraído (vía pdfplumber o similar).
    La extracción de texto del PDF la hace la capa de servicio, no esta función.

    El parsing específico de la constancia del SAT requiere un documento
    real para calibrar los patrones. La estructura es:
    - Encabezado con RFC y nombre
    - Sección "Régimen" con claves y fechas
    - Sección "Obligaciones" con periodicidad

    Args:
        texto_pdf: Texto completo extraído del PDF de la constancia.

    Returns:
        DatosConstancia con los datos extraídos.

    Raises:
        No lanza excepciones; los errores se reportan en DatosConstancia.error.
    """
    if not texto_pdf or not texto_pdf.strip():
        return DatosConstancia(
            rfc="", nombre="", tipo_persona="",
            valido=False, error="Texto de constancia vacío",
        )

    # TODO: implementar parsing real con documento de referencia.
    # Los patrones exactos dependen del formato del PDF del SAT
    # que varía entre años. Se necesita un documento real para calibrar.
    return DatosConstancia(
        rfc="", nombre="", tipo_persona="",
        valido=False,
        error="Parsing de constancia pendiente: se necesita documento real de referencia",
    )


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
