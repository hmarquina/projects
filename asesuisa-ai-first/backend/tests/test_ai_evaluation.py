import json
from pathlib import Path

from app.ai.evaluation import GOLDEN, evaluate
from app.ai.provider import CompletionRequest, MockProvider
from app.ai.requirement_schema import RequirementAnalysis


def test_golden_dataset_passes_thresholds() -> None:
    report = evaluate()
    assert report["passed"], report["failures"]
    assert report["cases"] >= 7


class _Regressed:
    """Simula un cambio de modelo/prompt que degrada la calidad: no detecta ambigüedades."""

    name, model = "mock", "regressed"

    def complete(self, request: CompletionRequest) -> str:
        out = RequirementAnalysis.model_validate_json(MockProvider().complete(request))
        return out.model_copy(
            update={"ambiguities": [], "score": 100, "ready": True}
        ).model_dump_json()


def test_evaluation_catches_regression() -> None:
    report = evaluate(_Regressed())
    assert report["passed"] is False
    assert report["metrics"]["ambiguity_recall"] < 0.9
    assert report["failures"]


def test_dataset_is_valid_and_synthetic() -> None:
    data = json.loads(Path(GOLDEN).read_text(encoding="utf-8"))
    ids = [c["id"] for c in data["cases"]]
    assert len(ids) == len(set(ids))
    assert "example.com" in json.dumps(data) and "@gmail" not in json.dumps(data)


def test_artifact_golden_dataset_passes_thresholds() -> None:
    from app.ai.evaluation import evaluate_artifacts

    report = evaluate_artifacts()
    assert report["passed"], report["failures"]
    assert set(report["metrics"]) >= {"traceability", "numeric_fidelity", "api_validity"}


class _Hallucinating:
    """Simula un modelo que inventa una cifra de disponibilidad en los criterios."""

    name, model = "mock", "hallucinating"

    def complete(self, request: CompletionRequest) -> str:
        raw = MockProvider().complete(request)
        if request.prompt_id == "acceptance_criteria":
            return raw.replace(
                "la operación se completa correctamente", "se garantiza 99.99% de disponibilidad", 1
            )
        return raw


def test_artifact_evaluation_detects_invented_numbers() -> None:
    from app.ai.evaluation import evaluate_artifacts

    report = evaluate_artifacts(_Hallucinating())
    assert report["passed"] is False
    assert report["metrics"]["numeric_fidelity"] < 1.0
    assert any("99.99" in f for f in report["failures"])


class _InsecureApi:
    """Simula un contrato sin respuestas 401/403."""

    name, model = "mock", "insecure"

    def complete(self, request: CompletionRequest) -> str:
        raw = MockProvider().complete(request)
        if request.prompt_id == "api_contract":
            return raw.replace('"401"', '"499"').replace('"403"', '"498"')
        return raw


def test_artifact_evaluation_detects_insecure_api() -> None:
    from app.ai.evaluation import evaluate_artifacts

    report = evaluate_artifacts(_InsecureApi())
    assert report["passed"] is False and report["metrics"]["api_validity"] < 1.0
