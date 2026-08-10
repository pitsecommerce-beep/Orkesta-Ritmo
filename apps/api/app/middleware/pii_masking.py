import re
import uuid
from typing import Optional


CURP_PATTERN = re.compile(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]{2}")
RFC_PATTERN = re.compile(r"[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}")
CLABE_PATTERN = re.compile(r"\b\d{18}\b")
ACCOUNT_PATTERN = re.compile(r"\b\d{10,16}\b")


class PIIMasker:
    def __init__(self):
        self._map: dict[str, str] = {}
        self._reverse: dict[str, str] = {}

    def mask(self, text: str) -> str:
        text = CURP_PATTERN.sub(self._replace_match("CURP"), text)
        text = RFC_PATTERN.sub(self._replace_match("RFC"), text)
        text = CLABE_PATTERN.sub(self._replace_match("CLABE"), text)
        text = ACCOUNT_PATTERN.sub(self._replace_match("CUENTA"), text)
        return text

    def _replace_match(self, category: str):
        def replacer(match: re.Match) -> str:
            original = match.group(0)
            if original in self._map:
                return self._map[original]
            token = f"[{category}_{uuid.uuid4().hex[:8]}]"
            self._map[original] = token
            self._reverse[token] = original
            return token
        return replacer

    def unmask(self, text: str) -> str:
        for token, original in self._reverse.items():
            text = text.replace(token, original)
        return text

    def has_pii(self, text: str) -> bool:
        return bool(
            RFC_PATTERN.search(text)
            or CLABE_PATTERN.search(text)
            or CURP_PATTERN.search(text)
        )


EFIRMA_KEYWORDS = [
    ".key", ".cer", "e.firma", "efirma", "fiel",
    "contraseña de la clave privada", "private key password",
]


def contains_efirma_material(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EFIRMA_KEYWORDS)
