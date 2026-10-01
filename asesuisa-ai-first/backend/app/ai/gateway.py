"""Model Gateway: único punto de acceso a modelos. Aplica política, guardrails y validación.

Application → AI Orchestration → Model Gateway → Provider.
Cambiar de proveedor, aplicar fallback o auditar uso no requiere tocar la aplicación.
"""

import logging
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app import audit
from app.ai import guardrails
from app.ai.prompts import get_prompt
from app.ai.provider import CompletionRequest, MockProvider, ModelProvider
from app.config import get_settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GatewayError(Exception):
    """Error controlado del gateway (proveedor no autorizado, salida inválida, etc.)."""


@dataclass
class GatewayResult(Generic[T]):
    output: T
    provider: str
    model: str
    prompt_label: str
    input_ref: str
    output_ref: str
    redactions: dict[str, int] = field(default_factory=dict)
    injection_flags: int = 0


class ModelGateway:
    def __init__(self, providers: list[ModelProvider], allowed: set[str]) -> None:
        unauthorized = {p.name for p in providers} - allowed
        if unauthorized:
            raise GatewayError(f"Uso de modelo no autorizado: {sorted(unauthorized)}")
        self._providers = providers

    def run(self, prompt_id: str, content: str, schema: type[T]) -> GatewayResult[T]:
        prompt = get_prompt(prompt_id)
        safe_content, redactions = guardrails.redact(content)  # el modelo nunca ve la PII
        injection = guardrails.detect_injection(safe_content)
        request = CompletionRequest(
            prompt_id=prompt.id,
            prompt_label=prompt.label,
            system=prompt.system,
            user_content=safe_content,
        )
        last_error: Exception | None = None
        for provider in self._providers:  # fallback ordenado
            try:
                raw = provider.complete(request)
                output = schema.model_validate_json(raw)  # salida no confiable hasta validar
            except (ValidationError, ValueError) as exc:
                log.warning("Proveedor %s falló o devolvió salida inválida", provider.name)
                last_error = exc
                continue
            return GatewayResult(
                output=output,
                provider=provider.name,
                model=provider.model,
                prompt_label=prompt.label,
                input_ref=audit.content_ref(safe_content),
                output_ref=audit.content_ref(raw),
                redactions=redactions,
                injection_flags=len(injection),
            )
        raise GatewayError("Ningún proveedor devolvió una salida válida") from last_error


def get_gateway() -> ModelGateway:
    name = get_settings().ai_provider
    if name != "mock":
        raise GatewayError(f"Proveedor '{name}' no configurado (solo 'mock' en el MVP)")
    return ModelGateway([MockProvider()], allowed={"mock"})
