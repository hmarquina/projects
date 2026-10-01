import json
from typing import Any

from fastapi.testclient import TestClient

from app.ai.provider import CompletionRequest, MockProvider

GOOD = (
    "El asegurado debe registrar un reclamo desde el portal web en menos de 3 minutos para "
    "recibir un número de seguimiento. El sistema deberá responder en menos de 2 segundos para "
    "el 95% de solicitudes, exigir autenticación y dejar trazabilidad en un log de auditoría. "
    "La disponibilidad mensual mínima será de 99.5% y el ajustador podrá consultar el estado "
    "del reclamo en cualquier momento."
)
KINDS = ["stories", "acceptance_criteria", "risks", "architecture", "api_contract"]


def ready_initiative(client: TestClient, login: Any, text: str = GOOD) -> int:
    a = login("analyst")
    iid = client.post("/initiatives", json={"title": "Reclamos", "description": text}, headers=a)
    iid = int(iid.json()["id"])
    assert client.post(f"/initiatives/{iid}/analyze", headers=a).status_code == 201
    for kind in KINDS:
        assert client.post(f"/initiatives/{iid}/artifacts/{kind}", headers=a).status_code == 201
    return iid


def run_pipeline(client: TestClient, login: Any, iid: int) -> dict[str, Any]:
    r = client.post(f"/initiatives/{iid}/pipeline", headers=login("tech_lead"))
    assert r.status_code == 201, r.text
    return dict(r.json())


class Tampering:
    """Proveedor que altera el código generado (simula un LLM defectuoso o malicioso)."""

    name, model = "mock", "tampering"

    def __init__(self, transform: Any) -> None:
        self.transform = transform

    def complete(self, request: CompletionRequest) -> str:
        raw = MockProvider().complete(request)
        if request.prompt_id != "code_skeleton":
            return raw
        data = json.loads(raw)
        data["files"]["generated_service/app.py"] = self.transform(
            data["files"]["generated_service/app.py"]
        )
        return json.dumps(data)
