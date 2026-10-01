"""Generador determinista de documentación del servicio (plantilla; no usa IA)."""

from typing import Any

REQUIRED_SECTIONS = (
    "## Requerimiento de origen",
    "## Operaciones",
    "## Criterios de aceptación y cobertura",
    "## Requisitos no funcionales",
    "## Riesgos y controles",
    "## Cómo ejecutar las pruebas",
    "## Limitaciones",
)


def generate_readme(
    title: str, spec: dict[str, Any], stories: dict[str, Any], criteria: list[dict[str, Any]],
    coverage: dict[str, str], risks: list[dict[str, Any]],
) -> str:  # fmt: skip
    ops = [
        f"| {m.upper()} | `{p}` | {op['summary']} |"
        for p, methods in spec["paths"].items()
        for m, op in methods.items()
    ]
    quotes = sorted({s["source_quote"] for s in stories["stories"]}
                    | {r["source_quote"] for r in stories["system_requirements"]})  # fmt: skip
    ac_rows = [
        f"| {c['id']} | {c['origin']} | {coverage.get(c['id'], 'manual')} |" for c in criteria
    ]
    nfr = [f"- {s}" for s in spec.get("x-nfr", [])] or ["- (el requerimiento no define cifras)"]
    risk_rows = [
        f"| {r['id']} | {r['category']} | {r['severity']} | {'; '.join(r['controls'])} |"
        for r in risks
    ]
    return "\n".join([
        f"# {title}", "",
        "> Borrador generado con asistencia de IA. Requiere revisión y aprobación humana.", "",
        "## Requerimiento de origen", "", *[f"> {q}" for q in quotes], "",
        "## Operaciones", "", "| Método | Ruta | Descripción |", "|---|---|---|", *ops, "",
        "Autenticación: JWT Bearer (HS256, secreto en `JWT_SECRET`). Roles: `reader`, `writer`, `approver`.",
        "", "## Criterios de aceptación y cobertura", "",
        "| Criterio | Origen | Cobertura |", "|---|---|---|", *ac_rows, "",
        "## Requisitos no funcionales", "", *nfr, "",
        "## Riesgos y controles", "", "| Id | Categoría | Severidad | Controles |", "|---|---|---|---|",
        *risk_rows, "",
        "## Cómo ejecutar las pruebas", "", "```bash", "pip install -r requirements.txt",
        "python -m pytest -q", "```", "",
        "## Limitaciones", "",
        "- Repositorio en memoria: sin persistencia real.",
        "- El smoke de tiempo de respuesta no sustituye una prueba de carga.",
        "- Los criterios `manual` requieren verificación operativa.", "",
    ])  # fmt: skip
