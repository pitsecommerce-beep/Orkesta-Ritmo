"""
Test que verifica que NO se usan float literals ni float() en el codigo fuente.

Usa inspeccion AST para escanear todos los archivos .py del paquete tax_engine
y falla si encuentra algun literal float o llamada a float() en codigo no-test.
"""

import ast
import os

import pytest


def _get_tax_engine_src_dir() -> str:
    """Obtiene el directorio src/tax_engine."""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(os.path.dirname(this_dir), "src", "tax_engine")
    return src_dir


def _find_python_files(directory: str) -> list[str]:
    """Encuentra todos los archivos .py en un directorio recursivamente."""
    py_files = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


class FloatDetector(ast.NodeVisitor):
    """Visitor AST que detecta uso de float."""

    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[str] = []

    def visit_Constant(self, node: ast.Constant) -> None:
        """Detecta literales float como 1.0, 0.16, etc."""
        if isinstance(node.value, float):
            self.violations.append(
                f"{self.filename}:{node.lineno}:{node.col_offset} - "
                f"Float literal encontrado: {node.value}"
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detecta llamadas a float()."""
        if isinstance(node.func, ast.Name) and node.func.id == "float":
            self.violations.append(
                f"{self.filename}:{node.lineno}:{node.col_offset} - "
                f"Llamada a float() encontrada"
            )
        self.generic_visit(node)


class TestNoFloats:
    """Verifica que el paquete tax_engine no usa float."""

    def test_no_float_literals_or_calls(self):
        """
        Escanea todos los archivos .py en src/tax_engine/ usando AST
        y falla si encuentra literales float o llamadas a float().

        Excluye archivos de test.
        """
        src_dir = _get_tax_engine_src_dir()
        py_files = _find_python_files(src_dir)

        assert len(py_files) > 0, (
            f"No se encontraron archivos .py en {src_dir}. "
            f"Verificar la estructura del paquete."
        )

        all_violations: list[str] = []

        for filepath in py_files:
            # Saltar archivos de test
            basename = os.path.basename(filepath)
            if basename.startswith("test_"):
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()

            try:
                tree = ast.parse(source, filename=filepath)
            except SyntaxError as e:
                pytest.fail(f"Error de sintaxis en {filepath}: {e}")

            detector = FloatDetector(filepath)
            detector.visit(tree)
            all_violations.extend(detector.violations)

        if all_violations:
            violation_report = "\n".join(all_violations)
            pytest.fail(
                f"Se encontraron {len(all_violations)} usos de float en "
                f"el paquete tax_engine (solo Decimal es permitido):\n\n"
                f"{violation_report}"
            )

    def test_source_files_exist(self):
        """Verifica que existen los archivos fuente esperados."""
        src_dir = _get_tax_engine_src_dir()
        expected_files = [
            "__init__.py",
            "types.py",
            "engine.py",
            "resico_pf.py",
            "arrendamiento.py",
            "resico_pm.py",
            "iva.py",
            "clasificador.py",
            "tarifas.py",
        ]

        for filename in expected_files:
            filepath = os.path.join(src_dir, filename)
            assert os.path.exists(filepath), (
                f"Archivo esperado no encontrado: {filepath}"
            )
