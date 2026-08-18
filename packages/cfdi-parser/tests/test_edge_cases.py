"""Tests de casos limite para subida manual de CFDI.

Verifica que el parser produce errores claros (nunca tracebacks crudos)
ante entradas malformadas: XML que no es CFDI, version no soportada,
XML truncado, archivo binario con extension .xml.
"""

from __future__ import annotations

from datetime import date

from cfdi_parser.source import ManualUploadSource, detect_and_parse


class TestXmlQueNoEsCfdi:
    """XML bien formado pero que no es un CFDI del SAT."""

    def test_xml_html(self):
        html = b"<html><body><p>Hola</p></body></html>"
        result = detect_and_parse(html)
        assert not result.es_valido
        assert any("no reconocido" in e for e in result.errores)

    def test_xml_rss(self):
        rss = b"""<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Feed</title></channel></rss>"""
        result = detect_and_parse(rss)
        assert not result.es_valido
        assert any("no reconocido" in e for e in result.errores)

    def test_xml_soap(self):
        soap = b"""<?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body><data>test</data></soap:Body>
        </soap:Envelope>"""
        result = detect_and_parse(soap)
        assert not result.es_valido


class TestVersionNoSoportada:
    """CFDI con version 3.3 (no soportada) en vez de 4.0."""

    def test_cfdi_33_produce_error_claro(self):
        cfdi_33 = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3"
            Version="3.3" TipoDeComprobante="I"
            SubTotal="100" Total="116" Moneda="MXN">
            <cfdi:Emisor Rfc="XAXX010101000" Nombre="TEST" RegimenFiscal="601"/>
            <cfdi:Receptor Rfc="XBXX020202000" Nombre="TEST" UsoCFDI="G03"/>
        </cfdi:Comprobante>"""
        result = detect_and_parse(cfdi_33)
        assert not result.es_valido
        assert any("no reconocido" in e for e in result.errores)

    def test_cfdi_33_no_lanza_excepcion(self):
        cfdi_33 = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3"
            Version="3.3" SubTotal="100" Total="116">
        </cfdi:Comprobante>"""
        result = detect_and_parse(cfdi_33)
        assert result.errores


class TestXmlTruncado:
    """XML cortado a la mitad (upload interrumpido)."""

    def test_xml_truncado_produce_error(self):
        truncado = b"""<?xml version="1.0"?>
        <cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
            Version="4.0" TipoDeComprobante="I"
            SubTotal="100" Total="116"""
        result = detect_and_parse(truncado)
        assert not result.es_valido
        assert any("mal formado" in e for e in result.errores)

    def test_xml_solo_declaracion(self):
        result = detect_and_parse(b'<?xml version="1.0"?>')
        assert not result.es_valido


class TestArchivoBinario:
    """Archivo binario con extension .xml."""

    def test_pdf_como_xml(self):
        pdf_header = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>"
        source = ManualUploadSource([("factura.xml", pdf_header)])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert not results[0].es_valido
        assert any("mal formado" in e for e in results[0].errores)

    def test_imagen_como_xml(self):
        png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        source = ManualUploadSource([("comprobante.xml", png_header)])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert not results[0].es_valido

    def test_archivo_vacio_xml(self):
        source = ManualUploadSource([("vacio.xml", b"")])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 1
        assert not results[0].es_valido


class TestSubidaMultipleMixta:
    """Mezcla de archivos validos e invalidos en una sola subida."""

    def test_mixta_no_contamina(self, ingreso_pue_xml):
        source = ManualUploadSource([
            ("bueno.xml", ingreso_pue_xml),
            ("malo.xml", b"<not valid"),
            ("foto.jpg", b"\xff\xd8\xff\xe0"),
        ])
        results = source.fetch("XAXX010101000", date(2024, 1, 1), date(2024, 12, 31))
        assert len(results) == 3
        assert results[0].es_valido
        assert not results[1].es_valido
        assert not results[2].es_valido
        assert "no soportado" in results[2].errores[0]
