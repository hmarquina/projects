"""Arnés de evaluación de IA: golden dataset, groundedness, consistencia y seguridad.

Uso: `python -m app.ai.evaluation [--provider mock]`. Sale con código 1 si algún umbral falla.
Cualquier cambio de prompt o de modelo debe pasar este arnés antes de promoverse (gate en CI).
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from app.ai import guardrails
from app.ai.artifact_schemas import (
    AcceptanceOutput,
    ApiContractOutput,
    ArchitectureOutput,
    RisksOutput,
    StoriesOutput,
)
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


GOLDEN_ARTIFACTS = GOLDEN.with_name("golden_artifacts.json")
_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(value: Any) -> set[str]:
    return set(_NUM.findall(json.dumps(value, ensure_ascii=False)))


def _api_problems(spec: dict[str, Any]) -> list[str]:
    from openapi_spec_validator import validate  # dependencia de dev/CI

    problems: list[str] = []
    try:
        validate(spec)
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de validación cuenta
        problems.append(f"OpenAPI inválido: {str(exc)[:120]}")
    if not spec.get("security"):
        problems.append("sin seguridad global")
    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            codes = set(op.get("responses", {}))
            if not {"401", "403"} <= codes:
                problems.append(f"{method.upper()} {path} sin 401/403")
    return problems


def evaluate_artifacts(
    provider: ModelProvider | None = None, dataset: Path = GOLDEN_ARTIFACTS
) -> dict[str, Any]:
    data = json.loads(dataset.read_text(encoding="utf-8"))
    gateway = ModelGateway(
        [provider or MockProvider()], allowed={(provider or MockProvider()).name}
    )
    keys = ("traceability", "numeric_fidelity", "story_recall", "ac_coverage", "risk_recall",
            "architecture_recall", "api_validity", "honesty", "consistency")  # fmt: skip
    counts = {k: [0, 0] for k in keys}
    failures: list[str] = []

    def check(bucket: str, ok: bool, case: str, detail: str) -> None:
        counts[bucket][1] += 1
        if ok:
            counts[bucket][0] += 1
        else:
            failures.append(f"{case}: {bucket} — {detail}")

    for case in data["cases"]:
        cid, text = case["id"], case["text"]
        low = text.lower()
        stories = gateway.run("user_stories", text, StoriesOutput).output
        ac = gateway.run("acceptance_criteria", text, AcceptanceOutput).output
        risks = gateway.run("risk_assessment", text, RisksOutput).output
        arch = gateway.run("architecture_proposal", text, ArchitectureOutput).output
        api = gateway.run("api_contract", text, ApiContractOutput).output

        quotes = (
            [s.source_quote for s in stories.stories]
            + [r.source_quote for r in stories.system_requirements]
            + [c.source_quote for c in ac.criteria]
        )
        for q in quotes:
            check("traceability", q in text, cid, f"cita inexistente: {q[:50]}")
        for r in risks.risks:
            ok = r.origin == "baseline" or r.evidence.lower() in low
            check("traceability", ok, cid, f"evidencia de riesgo inexistente: {r.evidence}")
        # Fidelidad numérica: toda cifra atribuida al requerimiento debe existir en él. Los AC
        # `baseline_control` (p. ej. "403") son controles de la organización y no se evalúan aquí.
        allowed = _numbers(text)
        claimed = {
            "AC": [[c.given, c.when, c.then, c.measurable_constraints]
                   for c in ac.criteria if c.origin == "requirement"],
            "historias": [[s.want, s.benefit] for s in stories.stories],
            "API x-nfr": api.openapi.get("x-nfr", []),
        }  # fmt: skip
        for label, payload in claimed.items():
            invented = _numbers(payload) - allowed
            check(
                "numeric_fidelity",
                not invented,
                cid,
                f"{label} con cifras inventadas: {sorted(invented)}",
            )

        found_actors = [s.actor for s in stories.stories]
        for actor in case["story_actors"]:
            check("story_recall", actor in found_actors, cid, f"falta historia de {actor}")
        per_story: dict[str, int] = {}
        for c in ac.criteria:
            per_story[c.story_id] = per_story.get(c.story_id, 0) + 1
        for s in stories.stories:
            check("ac_coverage", per_story.get(s.id, 0) >= 3, cid, f"{s.id} con menos de 3 AC")
        all_constraints = {x for c in ac.criteria for x in c.measurable_constraints}
        for cons in case["constraints"]:
            check("ac_coverage", cons in all_constraints, cid, f"restricción perdida: {cons}")
        for story_id in case["unconfirmed_benefit"]:
            st = next((s for s in stories.stories if s.id == story_id), None)
            check("honesty", st is not None and not st.benefit_confirmed, cid,
                  f"{story_id} debía marcarse sin beneficio confirmado")  # fmt: skip

        cats = {r.category for r in risks.risks}
        for cat in case["risk_categories"]:
            check("risk_recall", cat in cats, cid, f"falta riesgo '{cat}'")
        names = {c.name for c in arch.components}
        for name in case["components"]:
            check("architecture_recall", name in names, cid, f"falta componente '{name}'")
        for rel in arch.relations:
            ok = rel.source in names and rel.target in names
            check(
                "architecture_recall",
                ok,
                cid,
                f"relación con nodo inexistente {rel.source}→{rel.target}",
            )
        problems = _api_problems(api.openapi)
        check("api_validity", not problems, cid, "; ".join(problems))
        for path in case["api_paths"]:
            check("api_validity", path in api.openapi.get("paths", {}), cid, f"falta ruta {path}")

        again = (
            gateway.run("api_contract", text, ApiContractOutput).output == api
            and gateway.run("user_stories", text, StoriesOutput).output == stories
        )
        check("consistency", again, cid, "salida distinta ante la misma entrada")

    metrics = {k: (counts[k][0] / counts[k][1] if counts[k][1] else 1.0) for k in keys}
    passed = all(metrics[k] >= v for k, v in data["thresholds"].items())
    return {"passed": passed, "metrics": metrics, "failures": failures, "cases": len(data["cases"])}


def main() -> None:
    reports = {"requirements": evaluate(), "artifacts": evaluate_artifacts()}
    print(json.dumps(reports, indent=2, ensure_ascii=False))
    sys.exit(0 if all(r["passed"] for r in reports.values()) else 1)


if __name__ == "__main__":
    main()
