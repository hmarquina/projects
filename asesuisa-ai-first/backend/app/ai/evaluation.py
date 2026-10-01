"""Arnés de evaluación de IA: golden dataset, groundedness, consistencia y seguridad.

Uso: `python -m app.ai.evaluation [--provider mock]`. Sale con código 1 si algún umbral falla.
Cualquier cambio de prompt o de modelo debe pasar este arnés antes de promoverse (gate en CI).
"""

import json
import sys
from pathlib import Path
from typing import Any

from app.ai import guardrails
from app.ai.gateway import ModelGateway
from app.ai.provider import CompletionRequest, MockProvider, ModelProvider
from app.ai.requirement_schema import RequirementAnalysis

GOLDEN = Path(__file__).resolve().parents[2] / "evals" / "golden_requirements.json"


class _Spy:
    """Registra lo que el proveedor realmente recibe (para verificar que no llega PII)."""

    def __init__(self, inner: ModelProvider) -> None:
        self.inner, self.name, self.model = inner, inner.name, inner.model
        self.seen: list[str] = []

    def complete(self, request: CompletionRequest) -> str:
        self.seen.append(request.user_content)
        return self.inner.complete(request)


def _terms(analysis: RequirementAnalysis) -> set[str]:
    return {a.term.lower() for a in analysis.ambiguities}


def evaluate(provider: ModelProvider | None = None, dataset: Path = GOLDEN) -> dict[str, Any]:
    data = json.loads(dataset.read_text(encoding="utf-8"))
    spy = _Spy(provider or MockProvider())
    gateway = ModelGateway([spy], allowed={spy.name})
    counts = {k: [0, 0] for k in ("score", "recall", "ground", "consist", "security")}
    false_pos, failures = 0, []

    def check(bucket: str, ok: bool, case: str, detail: str) -> None:
        counts[bucket][1] += 1
        if ok:
            counts[bucket][0] += 1
        else:
            failures.append(f"{case}: {bucket} — {detail}")

    for case in data["cases"]:
        cid, text = case["id"], case["text"]
        res = gateway.run("requirement_quality", text, RequirementAnalysis)
        out = res.output
        redacted, _ = guardrails.redact(text)
        ok = case["min_score"] <= out.score <= case["max_score"]
        if "ready" in case:
            ok = ok and out.ready == case["ready"]
        check("score", ok, cid, f"score={out.score} ready={out.ready}")
        found = _terms(out)
        for term in case.get("must_flag", []):
            check("recall", term.lower() in found, cid, f"no detectó '{term}'")
        for term in case.get("must_not_flag", []):
            if term.lower() in found:
                false_pos += 1
                failures.append(f"{cid}: falso positivo '{term}'")
        for amb in out.ambiguities:  # groundedness: toda cita existe en el texto analizado
            grounded = amb.quote in redacted and amb.matched_text in amb.quote
            check("ground", grounded, cid, f"cita no fundamentada para '{amb.term}'")
        again = gateway.run("requirement_quality", text, RequirementAnalysis)
        check("consist", again.output == out, cid, "salida distinta ante la misma entrada")
        if "expect_pii" in case:
            kinds_ok = set(case["expect_pii"]) <= set(res.redactions)
            leaked = bool(guardrails.find_pii(spy.seen[-1]))
            check("security", kinds_ok and not leaked, cid, f"pii={res.redactions} leaked={leaked}")
        if case.get("expect_injection"):
            check("security", res.injection_flags > 0, cid, "no se señaló la inyección")

    def rate(key: str) -> float:
        ok, total = counts[key]
        return ok / total if total else 1.0

    metrics = {
        "score_accuracy": rate("score"),
        "ambiguity_recall": rate("recall"),
        "false_positives": false_pos,
        "groundedness": rate("ground"),
        "consistency": rate("consist"),
        "security": rate("security"),
    }
    th = data["thresholds"]
    passed = (
        all(metrics[k] >= th[k] for k in metrics if k != "false_positives")
        and metrics["false_positives"] <= th["false_positives"]
    )
    return {"passed": passed, "metrics": metrics, "failures": failures, "cases": len(data["cases"])}


def main() -> None:
    report = evaluate()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
