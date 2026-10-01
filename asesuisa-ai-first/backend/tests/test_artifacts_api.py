from fastapi.testclient import TestClient

GOOD = (
    "El asegurado debe registrar un reclamo desde el portal web en menos de 3 minutos para "
    "recibir un número de seguimiento. El sistema deberá responder en menos de 2 segundos para "
    "el 95% de solicitudes, exigir autenticación y dejar trazabilidad en un log de auditoría. "
    "La disponibilidad mensual mínima será de 99.5% y el ajustador podrá consultar el estado "
    "del reclamo en cualquier momento."
)
POOR = "El sistema debe ser rápido y fácil de usar, etc."
KINDS = ["stories", "acceptance_criteria", "risks", "architecture", "api_contract"]


def _setup(client: TestClient, h: dict[str, str], text: str, analyze: bool = True) -> int:
    iid = client.post("/initiatives", json={"title": "Reclamos", "description": text}, headers=h)
    iid = iid.json()["id"]
    if analyze:
        assert client.post(f"/initiatives/{iid}/analyze", headers=h).status_code == 201
    return int(iid)


def test_gate_blocks_without_analysis(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD, analyze=False)
    r = client.post(f"/initiatives/{iid}/artifacts/stories", headers=h)
    assert r.status_code == 409 and "análisis" in r.json()["detail"]


def test_gate_blocks_not_ready_requirement(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, POOR)
    r = client.post(f"/initiatives/{iid}/artifacts/stories", headers=h)
    assert r.status_code == 409 and "Definition of Ready" in r.json()["detail"]


def test_refine_requirement_then_generate(client: TestClient, login) -> None:  # noqa: ANN001
    """Flujo de la demo: requerimiento pobre → bloqueo → mejora → análisis → generación."""
    h = login("analyst")
    iid = _setup(client, h, POOR)
    assert client.post(f"/initiatives/{iid}/artifacts/risks", headers=h).status_code == 409
    assert (
        client.patch(f"/initiatives/{iid}", json={"description": GOOD}, headers=h).status_code
        == 200
    )
    assert client.post(f"/initiatives/{iid}/analyze", headers=h).json()["ready"] is True
    assert client.post(f"/initiatives/{iid}/artifacts/risks", headers=h).status_code == 201


def test_stale_analysis_blocks_after_edit(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD)
    client.patch(
        f"/initiatives/{iid}", json={"description": GOOD + " Se requiere algo más."}, headers=h
    )
    r = client.post(f"/initiatives/{iid}/artifacts/stories", headers=h)
    assert r.status_code == 409 and "vigente" in r.json()["detail"]


def test_all_kinds_generate_as_draft_with_traceability(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD)
    for kind in KINDS:
        r = client.post(f"/initiatives/{iid}/artifacts/{kind}", headers=h)
        assert r.status_code == 201, (kind, r.text)
        body = r.json()
        assert body["status"] == "draft" and body["version"] == 1
        assert body["model"] == "mock-heuristic-1" and body["prompt_label"].count("@") == 1
        assert body["requirement_ref"].startswith("sha256:")
    assert len(client.get(f"/initiatives/{iid}/artifacts", headers=login("viewer")).json()) == 5


def test_regeneration_increments_version(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD)
    client.post(f"/initiatives/{iid}/artifacts/stories", headers=h)
    r = client.post(f"/initiatives/{iid}/artifacts/stories", headers=h)
    assert r.json()["version"] == 2


def test_invalid_kind_rejected(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD)
    assert client.post(f"/initiatives/{iid}/artifacts/skynet", headers=h).status_code == 422


def test_rbac_on_generation(client: TestClient, login) -> None:  # noqa: ANN001
    iid = _setup(client, login("analyst"), GOOD)
    url = f"/initiatives/{iid}/artifacts/stories"
    assert client.post(url, headers=login("viewer")).status_code == 403
    assert client.post(url, headers=login("approver")).status_code == 403
    assert client.post(url).status_code == 401
    assert client.post(url, headers=login("tech_lead")).status_code == 201


def test_generation_is_audited_with_refs(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD)
    client.post(f"/initiatives/{iid}/artifacts/api_contract", headers=h)
    events = client.get("/audit", headers=login("security")).json()
    ev = next(e for e in events if e["action"] == "ai.generate.api_contract")
    assert ev["decision"] == "draft_created" and ev["resulting_artifact"].startswith("artifact:")
    assert ev["prompt_version"].startswith("api_contract@1.0.0+")
    assert ev["input_ref"].startswith("sha256:") and ev["output_ref"].startswith("sha256:")
    assert client.get("/audit/verify", headers=login("security")).json()["intact"] is True


def test_patch_rejects_pii_and_is_audited(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    iid = _setup(client, h, GOOD, analyze=False)
    r = client.patch(
        f"/initiatives/{iid}", json={"description": "Escribir a x@example.com"}, headers=h
    )
    assert r.status_code == 422
    assert (
        client.patch(f"/initiatives/{iid}", json={"title": "Nuevo título"}, headers=h).status_code
        == 200
    )
    events = client.get("/audit", headers=login("security")).json()
    assert any(e["action"] == "initiative.update" for e in events)


def test_patch_rbac_and_404(client: TestClient, login) -> None:  # noqa: ANN001
    iid = _setup(client, login("analyst"), GOOD, analyze=False)
    assert (
        client.patch(
            f"/initiatives/{iid}", json={"title": "abc"}, headers=login("viewer")
        ).status_code
        == 403
    )
    assert (
        client.patch(
            "/initiatives/999", json={"title": "abc"}, headers=login("analyst")
        ).status_code
        == 404
    )
