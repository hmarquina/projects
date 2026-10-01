from typing import Protocol

from pydantic import BaseModel

from app.ai import requirement_analyzer


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
        if request.prompt_id == "requirement_quality":
            return requirement_analyzer.analyze(request.user_content).model_dump_json()
        raise ValueError(f"El proveedor mock no soporta el prompt {request.prompt_id}")
