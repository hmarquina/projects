"""Controles de entrada para IA: detección/redacción de PII y señales de prompt injection.

Son heurísticas (control recomendado), no una garantía: se complementan con validación de la
salida, mínimo privilegio y revisión humana. Los patrones de PII locales (DUI, NIT, teléfono) son
ASSUMPTION de formato y deben validarse con Seguridad/Datos.
"""

import re
from dataclasses import dataclass

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("nit", re.compile(r"\b\d{4}-\d{6}-\d{3}-\d\b")),
    ("dui", re.compile(r"\b\d{8}-\d\b")),
    ("phone", re.compile(r"(?<![\d-])[267]\d{3}[- ]?\d{4}(?![\d-])")),
)
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")

_INJECTION: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignor[ae]\s+(?:todas?\s+)?(?:las\s+)?(?:instrucciones|reglas)",
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
        r"olvida\s+(?:todo|las\s+instrucciones)",
        r"revela\s+(?:tu|el)\s+(?:prompt|sistema)",
        r"(?:system|developer)\s+prompt",
        r"you\s+are\s+now\b",
        r"desactiva\s+(?:los\s+|las\s+)?(?:controles|filtros|reglas)",
        r"</?\s*(?:system|assistant)\s*>",
        r"(?:asigna|marca|pon)\w*\s+(?:un\s+)?(?:score|puntaje|puntuaci[oó]n)\s+(?:de\s+)?\d+",
    )
)


@dataclass(frozen=True)
class PiiFinding:
    kind: str
    start: int
    end: int


def _luhn_ok(raw: str) -> bool:
    digits = [int(c) for c in raw if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return total % 10 == 0


def find_pii(text: str) -> list[PiiFinding]:
    spans: list[PiiFinding] = []
    for kind, pattern in _PATTERNS:
        spans += [PiiFinding(kind, m.start(), m.end()) for m in pattern.finditer(text)]
    spans += [
        PiiFinding("card", m.start(), m.end()) for m in _CARD.finditer(text) if _luhn_ok(m.group())
    ]
    spans.sort(key=lambda f: (f.start, -(f.end - f.start)))
    result: list[PiiFinding] = []
    for f in spans:  # descarta solapes: gana el patrón más largo que empieza antes
        if not result or f.start >= result[-1].end:
            result.append(f)
    return result


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Sustituye PII por marcadores. Devuelve el texto y conteos por tipo (nunca los valores)."""
    counts: dict[str, int] = {}
    out, last = [], 0
    for f in find_pii(text):
        out.append(text[last : f.start])
        out.append(f"[PII:{f.kind.upper()}]")
        counts[f.kind] = counts.get(f.kind, 0) + 1
        last = f.end
    out.append(text[last:])
    return "".join(out), counts


def detect_injection(text: str) -> list[str]:
    return [p.pattern for p in _INJECTION if p.search(text)]
