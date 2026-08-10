import pytest
from app.middleware.pii_masking import PIIMasker, contains_efirma_material


class TestPIIMasker:
    def setup_method(self):
        self.masker = PIIMasker()

    def test_masks_rfc_persona_fisica(self):
        text = "El RFC del contribuyente es GARL850101AB1 y sus datos."
        masked = self.masker.mask(text)
        assert "GARL850101AB1" not in masked
        assert "[RFC_" in masked

    def test_masks_rfc_persona_moral(self):
        text = "Empresa con RFC ORL2301015A3 factura."
        masked = self.masker.mask(text)
        assert "ORL2301015A3" not in masked

    def test_masks_clabe(self):
        text = "CLABE interbancaria 012345678901234567 del titular."
        masked = self.masker.mask(text)
        assert "012345678901234567" not in masked
        assert "[CLABE_" in masked

    def test_masks_curp(self):
        text = "CURP: GARL850101HDFRRL09"
        masked = self.masker.mask(text)
        assert "GARL850101HDFRRL09" not in masked
        assert "[CURP_" in masked

    def test_masks_account_numbers(self):
        text = "Cuenta 1234567890123456 del banco."
        masked = self.masker.mask(text)
        assert "1234567890123456" not in masked

    def test_unmask_restores_original(self):
        text = "RFC GARL850101AB1 con CLABE 012345678901234567"
        masked = self.masker.mask(text)
        unmasked = self.masker.unmask(masked)
        assert "GARL850101AB1" in unmasked
        assert "012345678901234567" in unmasked

    def test_consistent_masking(self):
        text1 = "RFC GARL850101AB1 aparece aquí."
        text2 = "Y también GARL850101AB1 aquí."
        masked1 = self.masker.mask(text1)
        masked2 = self.masker.mask(text2)
        token = masked1.split("RFC ")[1].split(" ")[0]
        assert token in masked2

    def test_has_pii_detects_rfc(self):
        assert self.masker.has_pii("Texto con GARL850101AB1 dentro")

    def test_has_pii_detects_clabe(self):
        assert self.masker.has_pii("CLABE 012345678901234567")

    def test_has_pii_clean_text(self):
        assert not self.masker.has_pii("Texto sin datos personales")

    def test_rfc_never_crosses_to_ai(self):
        rfc_samples = [
            "XAXX010101000",
            "GARL850101AB1",
            "ORL2301015A3",
            "MELM8305281H4",
        ]
        for rfc in rfc_samples:
            text = f"El contribuyente {rfc} quiere declarar."
            masked = self.masker.mask(text)
            assert rfc not in masked, f"RFC {rfc} crossed masking boundary"

    def test_clabe_never_crosses_to_ai(self):
        clabes = [
            "012345678901234567",
            "002180700123456789",
            "014027000012345678",
        ]
        for clabe in clabes:
            text = f"Depósito a CLABE {clabe}"
            masked = self.masker.mask(text)
            assert clabe not in masked, f"CLABE {clabe} crossed masking boundary"


class TestEfirmaMaterialDetection:
    def test_detects_key_file(self):
        assert contains_efirma_material("Archivo prueba.key del SAT")

    def test_detects_cer_file(self):
        assert contains_efirma_material("Certificado prueba.cer")

    def test_detects_efirma_mention(self):
        assert contains_efirma_material("La e.firma del contribuyente")

    def test_detects_fiel_mention(self):
        assert contains_efirma_material("Necesito la FIEL para firmar")

    def test_detects_private_key_password(self):
        assert contains_efirma_material("contraseña de la clave privada es 1234")

    def test_clean_text_passes(self):
        assert not contains_efirma_material("Quiero calcular mi ISR")
