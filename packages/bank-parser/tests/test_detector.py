"""Tests para el auto-detector de institucion bancaria."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bank_parser.adapters.mercado_pago import MercadoPagoAdapter
from bank_parser.detector import detecta_institucion


class TestDetectorInstitucion:
    """Tests del detector automatico de institucion."""

    @patch("bank_parser.detector._extrae_texto_pdf")
    def test_detecta_mercado_pago(self, mock_extrae: MagicMock) -> None:
        mock_extrae.return_value = (
            "Mercado Pago - Estado de Cuenta\n"
            "Saldo inicial: $0.00\n"
            "Total de abonos: $100.00"
        )
        from pathlib import Path

        adaptador = detecta_institucion(Path("fake.pdf"))
        assert isinstance(adaptador, MercadoPagoAdapter)
        assert adaptador.institucion == "Mercado Pago"

    @patch("bank_parser.detector._extrae_texto_ocr")
    @patch("bank_parser.detector._extrae_texto_pdf")
    def test_no_reconoce_lanza_error(
        self, mock_extrae: MagicMock, mock_ocr: MagicMock,
    ) -> None:
        mock_extrae.return_value = "Documento cualquiera sin marcadores bancarios validos aqui"
        mock_ocr.return_value = "Documento cualquiera sin marcadores bancarios validos aqui"
        from pathlib import Path

        with pytest.raises(ValueError, match="No se reconoce"):
            detecta_institucion(Path("fake.pdf"))

    @patch("bank_parser.detector._extrae_texto_ocr")
    @patch("bank_parser.detector._extrae_texto_pdf")
    def test_error_incluye_instituciones_soportadas(
        self, mock_extrae: MagicMock, mock_ocr: MagicMock,
    ) -> None:
        mock_extrae.return_value = "Nada que ver con un banco ni una institucion financiera"
        mock_ocr.return_value = "Nada que ver con un banco ni una institucion financiera"
        from pathlib import Path

        with pytest.raises(ValueError, match="Mercado Pago"):
            detecta_institucion(Path("fake.pdf"))
