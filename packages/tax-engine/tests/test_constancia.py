"""Tests para extraccion de constancia de situacion fiscal."""

import os
from pathlib import Path

import pytest

from tax_engine.constancia import (
    DatosConstancia,
    ObligacionConstancia,
    RegimenConstancia,
    derivar_periodicidad,
    derivar_regimen_de_constancia,
    descripcion_a_clave_sat,
    extraer_constancia,
    extraer_constancia_desde_pdf,
    mapear_regimen_sat,
    normalizar_texto,
    parsear_fecha_espanol,
)


# --- Normalizacion de texto ---

class TestNormalizarTexto:
    """Normalizacion de descripciones para comparacion con catalogo."""

    def test_minusculas(self):
        assert normalizar_texto("ARRENDAMIENTO") == "arrendamiento"

    def test_sin_acentos(self):
        assert normalizar_texto("Régimen de Enajenación") == "regimen de enajenacion"

    def test_sin_punto_final(self):
        assert normalizar_texto("Arrendamiento.") == "arrendamiento"

    def test_espacios_colapsados(self):
        assert normalizar_texto("Sueldos   y   Salarios") == "sueldos y salarios"

    def test_combinado(self):
        result = normalizar_texto("  Régimen Simplificado de Confianza.  ")
        assert result == "regimen simplificado de confianza"

    def test_vacio(self):
        assert normalizar_texto("") == ""

    def test_enie(self):
        assert normalizar_texto("Año") == "ano"


# --- Catalogo descripcion -> clave SAT ---

class TestDescripcionAClaveSat:
    """Mapeo de descripciones de regimen a claves del catalogo c_RegimenFiscal."""

    def test_arrendamiento(self):
        assert descripcion_a_clave_sat("Arrendamiento") == "606"

    def test_arrendamiento_con_punto(self):
        assert descripcion_a_clave_sat("Arrendamiento.") == "606"

    def test_resico(self):
        assert descripcion_a_clave_sat("Régimen Simplificado de Confianza") == "626"

    def test_sueldos_salarios(self):
        assert descripcion_a_clave_sat(
            "Sueldos y Salarios e Ingresos Asimilados a Salarios"
        ) == "605"

    def test_general_ley(self):
        assert descripcion_a_clave_sat("General de Ley Personas Morales") == "601"

    def test_actividades_empresariales(self):
        assert descripcion_a_clave_sat(
            "Personas Físicas con Actividades Empresariales y Profesionales"
        ) == "612"

    def test_incorporacion_fiscal(self):
        assert descripcion_a_clave_sat("Incorporación Fiscal") == "621"

    def test_actividades_agricolas(self):
        assert descripcion_a_clave_sat(
            "Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras"
        ) == "622"

    def test_sin_obligaciones(self):
        assert descripcion_a_clave_sat("Sin Obligaciones Fiscales") == "616"

    def test_plataformas_tecnologicas(self):
        assert descripcion_a_clave_sat(
            "Régimen de las Actividades Empresariales con Ingresos a través de Plataformas Tecnológicas"
        ) == "625"

    def test_descripcion_desconocida(self):
        assert descripcion_a_clave_sat("Régimen Inventado") is None

    def test_mayusculas_completas(self):
        assert descripcion_a_clave_sat("ARRENDAMIENTO") == "606"

    def test_con_acentos_extra(self):
        assert descripcion_a_clave_sat("Régimen de Enajenación o Adquisición de Bienes") == "607"

    def test_variacion_textual_sat(self):
        """Bug 4: tolerar variaciones en el texto del SAT entre anios."""
        assert descripcion_a_clave_sat(
            "Régimen Simplificado de Confianza."
        ) == "626"


# --- Periodicidad ---

class TestDerivarPeriodicidad:
    """Derivacion de periodicidad a partir del texto de vencimiento."""

    def test_mensual(self):
        assert derivar_periodicidad("A más tardar el día 17 del mes inmediato posterior") == "mensual"

    def test_mensual_variante(self):
        assert derivar_periodicidad("Pago mensual") == "mensual"

    def test_bimestral(self):
        assert derivar_periodicidad("Pago bimestral") == "bimestral"

    def test_trimestral(self):
        assert derivar_periodicidad("Declaración trimestral") == "trimestral"

    def test_anual(self):
        assert derivar_periodicidad("Declaración anual") == "anual"

    def test_anual_variante(self):
        assert derivar_periodicidad("Anualmente en el mes de abril") == "anual"

    def test_sin_patron(self):
        assert derivar_periodicidad("Texto sin periodicidad") == "desconocida"

    def test_vacio(self):
        assert derivar_periodicidad("") == "desconocida"

    def test_prioridad_mensual_sobre_anual(self):
        assert derivar_periodicidad("Pago provisional mensual, declaración anual") == "mensual"

    def test_mes_inmediato_sin_espacio(self):
        """Bug 2: tolerar espacios colapsados del SAT."""
        assert derivar_periodicidad("mesinmediato posterior") == "mensual"


# --- Parsing de fechas en espanol ---

class TestParsearFechaEspanol:
    """Conversion de fechas en formato largo espanol a ISO."""

    def test_fecha_normal(self):
        assert parsear_fecha_espanol("01 DE OCTUBRE DE 2020") == "2020-10-01"

    def test_fecha_enero(self):
        assert parsear_fecha_espanol("15 DE ENERO DE 2022") == "2022-01-15"

    def test_fecha_diciembre(self):
        assert parsear_fecha_espanol("31 DE DICIEMBRE DE 2025") == "2025-12-31"

    def test_fecha_minusculas(self):
        assert parsear_fecha_espanol("01 de octubre de 2020") == "2020-10-01"

    def test_dia_sin_cero(self):
        assert parsear_fecha_espanol("5 DE MAYO DE 2023") == "2023-05-05"

    def test_no_es_fecha(self):
        assert parsear_fecha_espanol("texto cualquiera") == "texto cualquiera"

    def test_mes_invalido(self):
        assert parsear_fecha_espanol("01 DE MESFALSO DE 2020") == "01 DE MESFALSO DE 2020"


# --- Mapeo de claves SAT a regimen del sistema (corregido) ---

class TestMapeoRegimenSat:
    """Traduccion de claves SAT a regimenes del sistema."""

    def test_612_es_actividad_empresarial_no_resico(self):
        """Bug 3: 612 NO es RESICO, es Actividades Empresariales."""
        assert mapear_regimen_sat("612") is None

    def test_626_resico_pf_con_rfc_13(self):
        """Bug 3: 626 es RESICO PF cuando RFC tiene 13 caracteres."""
        assert mapear_regimen_sat("626", "XAXX010101000") == "RESICO_PF"

    def test_626_resico_pm_con_rfc_12(self):
        """Bug 3: 626 es RESICO PM cuando RFC tiene 12 caracteres."""
        assert mapear_regimen_sat("626", "XAX010101000") == "RESICO_PM"

    def test_626_default_sin_rfc(self):
        """626 sin RFC defaults a RESICO_PF."""
        assert mapear_regimen_sat("626") == "RESICO_PF"

    def test_arrendamiento(self):
        assert mapear_regimen_sat("606") == "ARRENDAMIENTO"

    def test_625_plataformas(self):
        """Bug 3: 625 es Plataformas Tecnologicas, no RESICO_PM."""
        assert mapear_regimen_sat("625") == "PLATAFORMAS_TECNOLOGICAS"

    def test_603_no_es_autotransporte(self):
        """Bug 3: 603 es Personas Morales sin Fines Lucrativos."""
        assert mapear_regimen_sat("603") is None

    def test_regimen_no_soportado(self):
        assert mapear_regimen_sat("601") is None

    def test_clave_inexistente(self):
        assert mapear_regimen_sat("999") is None

    def test_sueldos_salarios_retorna_valor(self):
        assert mapear_regimen_sat("605") == "SUELDOS_SALARIOS"


# --- Derivar regimen ---

class TestDerivarRegimen:
    """Derivacion de regimen desde datos de constancia."""

    def test_resico_pf_con_626(self):
        """626 debe derivar a RESICO_PF (RFC de 13 digitos)."""
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="626", descripcion="RESICO", fecha_alta="2022-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "RESICO_PF"

    def test_arrendamiento_unico(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="606", descripcion="Arrendamiento", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "ARRENDAMIENTO"

    def test_multiples_regimenes_arrendamiento_prioridad(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="626", descripcion="RESICO", fecha_alta="2022-01-01"),
                RegimenConstancia(clave_sat="606", descripcion="Arrendamiento", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "ARRENDAMIENTO"

    def test_ningun_regimen_soportado(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="601", descripcion="General", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) is None

    def test_sin_regimenes(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
        )
        assert derivar_regimen_de_constancia(datos) is None

    def test_regimen_no_vigente_ignorado(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="626", descripcion="RESICO", fecha_alta="2022-01-01", vigente=False),
            ],
        )
        assert derivar_regimen_de_constancia(datos) is None

    def test_plataformas_625_a_lista_espera(self):
        """625 debe retornar PLATAFORMAS_TECNOLOGICAS para enviar a lista de espera."""
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="625", descripcion="Plataformas", fecha_alta="2022-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "PLATAFORMAS_TECNOLOGICAS"

    def test_resico_pf_con_sueldos(self):
        """RESICO + Sueldos debe retornar RESICO_PF_SUELDOS."""
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="626", descripcion="RESICO", fecha_alta="2022-01-01"),
                RegimenConstancia(clave_sat="605", descripcion="Sueldos", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "RESICO_PF_SUELDOS"

    def test_arrendamiento_con_sueldos(self):
        """Arrendamiento + Sueldos debe retornar ARRENDAMIENTO_SUELDOS."""
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[
                RegimenConstancia(clave_sat="606", descripcion="Arrendamiento", fecha_alta="2020-01-01"),
                RegimenConstancia(clave_sat="605", descripcion="Sueldos", fecha_alta="2020-01-01"),
            ],
        )
        assert derivar_regimen_de_constancia(datos) == "ARRENDAMIENTO_SUELDOS"


# --- Bug 5: valido con regimenes vacios ---

class TestValidoConRegimenesVacios:
    """Bug 5: DatosConstancia.valido no debe ser True si hay tabla de regimenes pero cero extraidos."""

    def test_valido_sin_tabla_de_regimenes(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[],
            regimenes_tabla_presente=False,
        )
        assert datos.valido is True

    def test_invalido_con_tabla_pero_sin_regimenes(self):
        datos = DatosConstancia(
            rfc="XAXX010101000", nombre="Test", tipo_persona="fisica",
            regimenes=[],
            regimenes_tabla_presente=True,
            valido=False,
            error="Constancia tiene tabla de regimenes pero no se pudo extraer ninguno",
        )
        assert datos.valido is False


# --- Extraccion de texto plano ---

class TestExtraerNombreDeTablasBug2:
    """Bug 2: _extraer_nombre_de_tablas debe tolerar etiquetas concatenadas sin espacio."""

    def test_etiquetas_con_espacio(self):
        from tax_engine.constancia import _extraer_nombre_de_tablas
        tablas = [[
            ["Nombre (s):", "FRANCISCO JAVIER"],
            ["Primer Apellido:", "TALLABS"],
            ["Segundo Apellido:", "UTRILLA"],
        ]]
        nombre = _extraer_nombre_de_tablas(tablas)
        assert nombre == "FRANCISCO JAVIER TALLABS UTRILLA"

    def test_etiquetas_sin_espacio_concatenadas(self):
        """Bug 2: el PDF real produce 'PrimerApellido:' sin espacio."""
        from tax_engine.constancia import _extraer_nombre_de_tablas
        tablas = [[
            ["Nombre(s):", "FRANCISCOJAVIER"],
            ["PrimerApellido:", "TALLABS"],
            ["SegundoApellido:", "UTRILLA"],
        ]]
        nombre = _extraer_nombre_de_tablas(tablas)
        assert nombre == "FRANCISCOJAVIER TALLABS UTRILLA"

    def test_etiquetas_mixtas(self):
        from tax_engine.constancia import _extraer_nombre_de_tablas
        tablas = [[
            ["Nombre (s):", "JUAN"],
            ["PrimerApellido:", "PEREZ"],
            ["Segundo Apellido:", "GARCIA"],
        ]]
        nombre = _extraer_nombre_de_tablas(tablas)
        assert nombre == "JUAN PEREZ GARCIA"

    def test_razon_social(self):
        from tax_engine.constancia import _extraer_nombre_de_tablas
        tablas = [[
            ["Denominacion/RazonSocial:", "EMPRESA SA DE CV"],
        ]]
        nombre = _extraer_nombre_de_tablas(tablas)
        assert nombre == "EMPRESA SA DE CV"


class TestExtraerConstanciaTexto:
    """Extraccion de datos a partir de texto plano."""

    def test_texto_vacio(self):
        datos = extraer_constancia("")
        assert not datos.valido
        assert "vacío" in datos.error

    def test_texto_solo_espacios(self):
        datos = extraer_constancia("   ")
        assert not datos.valido

    def test_sin_datos_reconocibles(self):
        datos = extraer_constancia("Texto sin estructura reconocible")
        assert not datos.valido
        assert "No se pudo extraer" in datos.error

    def test_con_rfc_persona_fisica(self):
        texto = """
        SERVICIO DE ADMINISTRACIÓN TRIBUTARIA
        Constancia de Situación Fiscal
        RFC : XAXX010101000
        Nombre (s) : JUAN
        """
        datos = extraer_constancia(texto)
        assert datos.valido
        assert datos.rfc == "XAXX010101000"
        assert datos.tipo_persona == "fisica"
        assert datos.nombre == "JUAN"

    def test_con_rfc_persona_moral(self):
        texto = """
        RFC : XAX010101000
        Denominación o Razón Social : EMPRESA SA DE CV
        """
        datos = extraer_constancia(texto)
        assert datos.valido
        assert datos.rfc == "XAX010101000"
        assert datos.tipo_persona == "moral"

    def test_con_codigo_postal(self):
        texto = """
        RFC : XAXX010101000
        Nombre (s) : TEST
        Código Postal : 06600
        """
        datos = extraer_constancia(texto)
        assert datos.domicilio_cp == "06600"

    def test_con_fecha_inicio(self):
        texto = """
        RFC : XAXX010101000
        Nombre (s) : TEST
        Fecha de inicio de operaciones : 01 DE OCTUBRE DE 2020
        """
        datos = extraer_constancia(texto)
        assert datos.valido

    def test_rfc_sin_espacio_bug2(self):
        """Bug 2: pdfplumber colapsa espacios."""
        texto = "RFC:XAXX010101000\nNombre(s):JUAN"
        datos = extraer_constancia(texto)
        assert datos.rfc == "XAXX010101000"

    def test_codigo_postal_sin_espacio(self):
        """Bug 2: CódigoPostal:62160 sin espacio."""
        texto = "RFC:XAXX010101000\nCódigoPostal:62160"
        datos = extraer_constancia(texto)
        assert datos.domicilio_cp == "62160"


# --- Extraccion desde PDF real (skip si no hay fixture) ---

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CONSTANCIA_PF_PDF = FIXTURES_DIR / "constancia_pf.pdf"
CONSTANCIA_PM_PDF = FIXTURES_DIR / "constancia_pm.pdf"


@pytest.mark.skipif(
    not CONSTANCIA_PF_PDF.exists(),
    reason="Fixture constancia_pf.pdf no disponible (PII, no se sube al repo)",
)
class TestExtraerConstanciaPdfPf:
    """Tests con PDF real de persona fisica. Solo corren si el fixture existe."""

    def test_extrae_rfc(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PF_PDF)
        assert datos.valido
        assert len(datos.rfc) == 13

    def test_tipo_persona_fisica(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PF_PDF)
        assert datos.tipo_persona == "fisica"

    def test_tiene_regimenes(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PF_PDF)
        assert len(datos.regimenes) > 0

    def test_tiene_obligaciones(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PF_PDF)
        assert len(datos.obligaciones) > 0


@pytest.mark.skipif(
    not CONSTANCIA_PM_PDF.exists(),
    reason="Fixture constancia_pm.pdf no disponible (PII, no se sube al repo)",
)
class TestExtraerConstanciaPdfPm:
    """Tests con PDF real de persona moral. Solo corren si el fixture existe."""

    def test_extrae_rfc(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PM_PDF)
        assert datos.valido
        assert len(datos.rfc) == 12

    def test_tipo_persona_moral(self):
        datos = extraer_constancia_desde_pdf(CONSTANCIA_PM_PDF)
        assert datos.tipo_persona == "moral"


# --- extraer_constancia_desde_pdf: edge cases ---

class TestExtraerConstanciaDesdePdfEdgeCases:
    """Edge cases de la funcion de extraccion desde PDF."""

    def test_archivo_no_existe(self):
        datos = extraer_constancia_desde_pdf("/ruta/que/no/existe.pdf")
        assert not datos.valido
        assert "no encontrado" in datos.error.lower()

    def test_archivo_no_es_pdf(self, tmp_path):
        archivo = tmp_path / "no_es_pdf.pdf"
        archivo.write_text("esto no es un PDF")
        datos = extraer_constancia_desde_pdf(archivo)
        assert not datos.valido


# --- Test contra PDF plantilla ---

PLANTILLA_PDF = Path("/root/.claude/uploads/807972f3-f515-52f1-a9e2-81701d373790/9f6ad0c3-Constancia_PLANTILLA_sin_datos_reales.pdf")


@pytest.mark.skipif(
    not PLANTILLA_PDF.exists(),
    reason="PDF plantilla no disponible en esta sesion",
)
class TestExtraerConstanciaPlantilla:
    """Tests contra el PDF plantilla sintetico."""

    def test_extrae_rfc(self):
        datos = extraer_constancia_desde_pdf(PLANTILLA_PDF)
        assert datos.rfc == "XXXX000000XX0"

    def test_nombre_compuesto(self):
        datos = extraer_constancia_desde_pdf(PLANTILLA_PDF)
        assert "[NOMBRE]" in datos.nombre
        assert "[APELLIDO1]" in datos.nombre

    def test_regimenes_separados_de_obligaciones(self):
        """Bug 1: textos de vencimiento no deben aparecer como regimenes."""
        datos = extraer_constancia_desde_pdf(PLANTILLA_PDF)
        assert len(datos.regimenes) == 2
        for r in datos.regimenes:
            assert "VENCIMIENTO" not in r.descripcion

    def test_obligaciones_correctas(self):
        datos = extraer_constancia_desde_pdf(PLANTILLA_PDF)
        assert len(datos.obligaciones) == 3

    def test_tabla_regimenes_encontrada(self):
        datos = extraer_constancia_desde_pdf(PLANTILLA_PDF)
        assert datos.regimenes_tabla_presente is True
