"""Analizador determinista de calidad de requerimientos (lo ejecuta el proveedor mock).

Es una heurística transparente y reproducible, NO un LLM. Con un proveedor real, el mismo esquema
de salida y el mismo arnés de evaluación (`evaluation.py`) permiten comparar modelos.
"""

import re

from app.ai.requirement_schema import Ambiguity, DimensionScore, RequirementAnalysis

READY_THRESHOLD = 75

_VAGUE: dict[str, tuple[str, str]] = {
    "rápido": ("No define un tiempo", "¿Cuál es el tiempo de respuesta máximo aceptable?"),
    "rapido": ("No define un tiempo", "¿Cuál es el tiempo de respuesta máximo aceptable?"),
    "fácil": ("Subjetivo, no verificable", "¿Qué tarea debe completarse y en cuántos pasos?"),
    "facil": ("Subjetivo, no verificable", "¿Qué tarea debe completarse y en cuántos pasos?"),
    "intuitivo": ("Subjetivo, no verificable", "¿Con qué prueba de usabilidad se validará?"),
    "amigable": ("Subjetivo, no verificable", "¿Con qué criterio de usabilidad se validará?"),
    "eficiente": ("No define una métrica", "¿Qué métrica y umbral definen 'eficiente'?"),
    "óptimo": ("No define una métrica", "¿Qué métrica y umbral definen 'óptimo'?"),
    "adecuado": ("Criterio no definido", "¿Qué criterio concreto determina que es adecuado?"),
    "flexible": ("Alcance no acotado", "¿Qué variaciones concretas debe soportar?"),
    "robusto": ("No verificable", "¿Qué nivel de disponibilidad o tolerancia a fallos se exige?"),
    "etc": ("Lista abierta; alcance indefinido", "¿Cuáles son todos los elementos incluidos?"),
    "y/o": ("Combinación ambigua", "¿Se requieren ambos casos o basta uno?"),
    "según corresponda": ("Regla no explícita", "¿Qué regla determina cada caso?"),
    "lo antes posible": ("Sin plazo", "¿Cuál es el plazo máximo?"),
    "tiempo razonable": ("Sin plazo", "¿Cuál es el plazo máximo?"),
    "algunos": ("Cantidad indefinida", "¿Cuántos o cuáles exactamente?"),
    "varios": ("Cantidad indefinida", "¿Cuántos o cuáles exactamente?"),
    "mejor": ("Comparación sin referencia", "¿Mejor respecto de qué base y métrica?"),
}
_ACTOR = re.compile(
    r"\b(?:el|la)\s+(?:usuario|asegurado|cliente|ajustador|sistema|analista|compañía|"
    r"corredor|beneficiario|supervisor|operador)\b",
    re.IGNORECASE,
)
_OBLIGATION = re.compile(r"\b(?:debe|deber[áa]|deben|permit\w+|podr[áa])\b", re.IGNORECASE)
_MEASURABLE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:%|ms|segundos?|minutos?|horas?|d[ií]as?|usuarios?|"
    r"solicitudes?|mb|gb|veces)",
    re.IGNORECASE,
)
_NFR: dict[str, re.Pattern[str]] = {
    "seguridad": re.compile(r"autentic|autoriz|cifrad|encript|seguridad", re.IGNORECASE),
    "rendimiento": re.compile(r"respon\w+|latencia|rendimiento|concurren", re.IGNORECASE),
    "disponibilidad": re.compile(r"disponibilidad|continuidad|recuperaci", re.IGNORECASE),
    "auditoría": re.compile(r"auditor|trazabilidad|bit[áa]cora|\blog\b", re.IGNORECASE),
}
_WEIGHTS = {
    "claridad": 30,
    "medibilidad": 25,
    "actor": 15,
    "obligación": 10,
    "no_funcionales": 10,
    "completitud": 10,
}
_QUESTIONS = {
    "medibilidad": "Falta al menos un criterio medible (tiempo, porcentaje, volumen).",
    "actor": "No se identifica quién realiza o recibe la funcionalidad.",
    "obligación": "No se expresa qué debe hacer el sistema (usar 'debe'/'deberá').",
    "no_funcionales": "Faltan requisitos no funcionales (seguridad, rendimiento, auditoría).",
    "completitud": "El requerimiento es demasiado breve para ser implementable.",
}


def _term_pattern(term: str) -> str:
    """Admite variantes de género y número (intuitivo/intuitiva/intuitivos)."""
    if " " in term or not term[-1].isalnum():
        return re.escape(term)
    if term.endswith("os"):
        return re.escape(term[:-2]) + "[oa]s"
    if term.endswith("o"):
        return re.escape(term[:-1]) + "[oa]s?"
    if term.endswith(("e", "l")):
        return re.escape(term) + "(?:es|s)?"
    return re.escape(term)


def _find_term(text: str, term: str) -> re.Match[str] | None:
    return re.search(rf"(?<!\w){_term_pattern(term)}(?!\w)", text, re.IGNORECASE)


def _sentence_around(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    ends = [i for i in (text.find(".", end), text.find("\n", end)) if i != -1]
    right = min(ends) + 1 if ends else len(text)
    return text[left:right].strip()[:500]


def analyze(text: str) -> RequirementAnalysis:
    ambiguities: list[Ambiguity] = []
    seen: set[str] = set()
    for term, (reason, question) in _VAGUE.items():
        m = _find_term(text, term)
        if not m or reason + question in seen:
            continue
        seen.add(reason + question)
        ambiguities.append(
            Ambiguity(
                term=term,
                matched_text=m.group(),
                quote=_sentence_around(text, m.start(), m.end()),
                reason=reason,
                clarifying_question=question,
            )
        )
    measurable = len(_MEASURABLE.findall(text))
    nfr_hits = sum(1 for p in _NFR.values() if p.search(text))
    words = len(text.split())
    raw = {
        "claridad": max(0, 100 - 25 * len(ambiguities)),
        "medibilidad": 0 if measurable == 0 else 60 if measurable == 1 else 100,
        "actor": 100 if _ACTOR.search(text) else 0,
        "obligación": 100 if _OBLIGATION.search(text) else 0,
        "no_funcionales": min(100, nfr_hits * 50),
        "completitud": min(100, round(words / 40 * 100)),
    }
    score = round(sum(raw[k] * w for k, w in _WEIGHTS.items()) / 100)
    rating = "insuficiente" if score < 40 else "mejorable" if score < READY_THRESHOLD else "listo"
    return RequirementAnalysis(
        score=score,
        rating=rating,
        ready=score >= READY_THRESHOLD,
        dimensions=[DimensionScore(name=k, score=raw[k], weight=w) for k, w in _WEIGHTS.items()],
        ambiguities=ambiguities,
        missing=[_QUESTIONS[k] for k in _QUESTIONS if raw[k] == 0],
    )


# Alias públicos para los generadores de artefactos.
ACTOR_RE, OBLIGATION_RE, MEASURABLE_RE = _ACTOR, _OBLIGATION, _MEASURABLE
NFR_PATTERNS = _NFR
