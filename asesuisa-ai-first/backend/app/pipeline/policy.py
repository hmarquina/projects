"""Política estática previa a la ejecución del código generado (barrera contra agencia excesiva).

Aplica a TODO código generado, venga de plantillas o de un LLM. Lista blanca de imports, sin
llamadas dinámicas peligrosas y sin atributos de escape. Es una defensa en profundidad: no
reemplaza el aislamiento por contenedor que se exigiría en producción.
"""

import ast
from dataclasses import dataclass

ALLOWED_IMPORTS = frozenset({
    "__future__", "collections", "datetime", "fastapi", "generated_service", "json", "jwt",
    "logging", "os", "pathlib", "pydantic", "pytest", "re", "secrets", "starlette", "tests",
    "time", "typing", "uuid",
})  # fmt: skip
FORBIDDEN_CALLS = frozenset({"eval", "exec", "compile", "__import__", "open", "input", "breakpoint",
                             "globals", "locals", "vars", "setattr", "delattr"})  # fmt: skip
FORBIDDEN_ATTRS = frozenset({"__class__", "__subclasses__", "__globals__", "__builtins__",
                             "__bases__", "__mro__", "__code__", "__dict__"})  # fmt: skip


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    rule: str


def check_source(path: str, source: str) -> list[Violation]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [Violation(path, exc.lineno or 0, "sintaxis inválida")]
    found: list[Violation] = []

    def add(node: ast.AST, rule: str) -> None:
        found.append(Violation(path, getattr(node, "lineno", 0), rule))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    add(node, f"import no permitido: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level or root not in ALLOWED_IMPORTS:
                add(node, f"import no permitido: {node.module or '.'}")
            if root == "os" and any(a.name != "environ" for a in node.names):
                add(node, "de `os` solo se permite `environ`")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                add(node, f"llamada prohibida: {node.func.id}()")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                add(node, f"atributo prohibido: {node.attr}")
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr != "environ"
            ):
                add(node, f"os.{node.attr} no permitido (solo os.environ)")
    return found


def check_files(files: dict[str, str]) -> list[Violation]:
    out: list[Violation] = []
    for path, source in sorted(files.items()):
        if path.endswith(".py"):
            out += check_source(path, source)
    return out
