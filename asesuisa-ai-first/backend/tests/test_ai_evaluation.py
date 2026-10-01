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
