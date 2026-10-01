from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel
from pydantic import BaseModel as _Model

from app.ai import artifact_generators as gen
from app.ai import requirement_analyzer
from app.pipeline import codegen, testgen


class CompletionRequest(BaseModel):
    prompt_id: str
    prompt_label: str
    system: str
    user_content: str


class ModelProvider(Protocol):
    name: str
    model: str

    def complete(self, request: CompletionRequest) -> str: ...


class MockProvider:
    """Proveedor determinista y offline. No es un LLM: ejecuta analizadores heurísticos."""

    name = "mock"
    model = "mock-heuristic-1"

    def complete(self, request: CompletionRequest) -> str:
        handler = _HANDLERS.get(request.prompt_id)
        if handler is None:
            raise ValueError(f"El proveedor mock no soporta el prompt {request.prompt_id}")
        return handler(request.user_content).model_dump_json()


_HANDLERS: dict[str, Callable[[str], _Model]] = {
    "requirement_quality": requirement_analyzer.analyze,
    "user_stories": gen.derive_stories,
    "acceptance_criteria": gen.derive_acceptance,
    "risk_assessment": gen.derive_risks,
    "architecture_proposal": gen.derive_architecture,
    "api_contract": gen.derive_api_contract,
    "code_skeleton": codegen.generate,
    "test_generation": testgen.generate,
}
