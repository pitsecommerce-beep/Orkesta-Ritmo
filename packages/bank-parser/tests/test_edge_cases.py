"""Tests de casos limite para subida de estados de cuenta.

Verifica que el parser bancario produce errores claros ante entradas
malformadas: archivo vacio, formato no reconocido, adaptador no
implementado. Ningun caso debe producir un traceback crudo.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bank_parser.adapters.mercado_pago import parsea_texto_mercado_pago
from bank_parser.detector import detecta_institucion


class TestTextoVacio:
    """Estado de cuenta vacio o sin contenido util."""

    def test_texto_vacio_no_crashea(self):
        resultado = parsea_texto_mercado_pago("")
        assert resultado.institucion == "Mercado Pago"
        assert len(resultado.movimientos) == 0

    def test_texto_solo_espacios(self):
        resultado = parsea_texto_mercado_pago("   \n\n   \n")
        assert len(resultado.movimientos) == 0


class TestFormatoNoReconocido:
    """Archivo que ningun adaptador reconoce."""

    def test_texto_aleatorio_no_reconocido(self, tmp_path):
        archivo = tmp_path / "basura.pdf"
        archivo.write_bytes(b"%PDF-1.4 contenido aleatorio sin estructura")
        with patch("bank_parser.detector._extrae_texto_pdf",
                    return_value="Texto completamente irrelevante sin banco"):
            with patch("bank_parser.detector._extrae_texto_ocr",
                        return_value="Texto completamente irrelevante sin banco"):
                with pytest.raises(ValueError, match="No se reconoce"):
                    detecta_institucion(archivo)

    def test_error_lista_instituciones_soportadas(self, tmp_path):
        archivo = tmp_path / "otro.pdf"
        archivo.write_bytes(b"%PDF-1.4")
        with patch("bank_parser.detector._extrae_texto_pdf",
                    return_value="nada que matchee"):
            with patch("bank_parser.detector._extrae_texto_ocr",
                        return_value="nada que matchee"):
                with pytest.raises(ValueError) as exc_info:
                    detecta_institucion(archivo)
                msg = str(exc_info.value)
                assert "Mercado Pago" in msg
                assert "Santander" in msg


class TestAdaptadorNoImplementado:
    """Verificar que adaptadores esqueleto fallan con mensaje claro."""

    def test_santander_archivo_invalido(self):
        from bank_parser.adapters.santander import SantanderAdapter
        with pytest.raises(Exception):
            SantanderAdapter().parsea(Path("/fake"))

    def test_bbva_no_implementado(self):
        from bank_parser.adapters.bbva import BBVAAdapter
        with pytest.raises(NotImplementedError, match="BBVA"):
            BBVAAdapter().parsea(Path("/fake"))

    def test_nu_no_implementado(self):
        from bank_parser.adapters.nu import NuAdapter
        with pytest.raises(NotImplementedError, match="Nu"):
            NuAdapter().parsea(Path("/fake"))

    def test_revolut_no_implementado(self):
        from bank_parser.adapters.revolut import RevolutAdapter
        with pytest.raises(NotImplementedError, match="Revolut"):
            RevolutAdapter().parsea(Path("/fake"))


class TestEncabezadoMercadoPagoIncompleto:
    """Mercado Pago con encabezado parcial o corrupto."""

    def test_sin_titular(self):
        texto = """Mercado Pago - Estado de Cuenta
CVU: 0000007702834561234567
Periodo: 01/10/2025 al 31/10/2025
Saldo inicial: $1,000.00
Saldo final: $1,000.00
Total de abonos: $0.00
Total de cargos: $0.00
Comisiones: $0.00

Movimientos
"""
        resultado = parsea_texto_mercado_pago(texto)
        assert resultado.institucion == "Mercado Pago"

    def test_sin_periodo(self):
        texto = """Mercado Pago - Estado de Cuenta
Titular: JUAN PEREZ
CVU: 0000007702834561234567
Saldo inicial: $500.00
Saldo final: $500.00
Total de abonos: $0.00
Total de cargos: $0.00
Comisiones: $0.00

Movimientos
"""
        resultado = parsea_texto_mercado_pago(texto)
        assert resultado.institucion == "Mercado Pago"

    def test_montos_no_numericos_en_encabezado(self):
        texto = """Mercado Pago - Estado de Cuenta
Titular: JUAN PEREZ
CVU: 0000007702834561234567
Periodo: 01/10/2025 al 31/10/2025
Saldo inicial: CORRUPTO
Saldo final: $0.00
Total de abonos: $0.00
Total de cargos: $0.00
Comisiones: $0.00

Movimientos
"""
        resultado = parsea_texto_mercado_pago(texto)
        assert resultado.institucion == "Mercado Pago"
