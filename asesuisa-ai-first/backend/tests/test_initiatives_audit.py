from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import engine


def _create(client: TestClient, headers: dict[str, str], title: str = "Reclamos digitales"):  # noqa: ANN202
    return client.post(
        "/initiatives", json={"title": title, "description": "Sintético"}, headers=headers
    )


def test_create_and_list(client: TestClient, login) -> None:  # noqa: ANN001
    r = _create(client, login("analyst"))
    assert r.status_code == 201
    assert r.json()["created_by"] == "demo_analyst"
    listed = client.get("/initiatives", headers=login("viewer")).json()
    assert [i["title"] for i in listed] == ["Reclamos digitales"]


def test_get_missing_is_404(client: TestClient, login) -> None:  # noqa: ANN001
    assert client.get("/initiatives/999", headers=login("viewer")).status_code == 404


def test_input_validation(client: TestClient, login) -> None:  # noqa: ANN001
    h = login("analyst")
    assert _create(client, h, "ab").status_code == 422
    assert _create(client, h, "x" * 201).status_code == 422


def test_audit_records_actor_and_hashes_input(client: TestClient, login) -> None:  # noqa: ANN001
    _create(client, login("analyst"))
    events = client.get("/audit", headers=login("security")).json()
    create = next(e for e in events if e["action"] == "initiative.create")
    assert create["user"] == "demo_analyst"
    assert create["role"] == "analyst"
    assert create["input_ref"].startswith("sha256:")
    assert "Reclamos" not in str(create)  # no se almacena el contenido
    assert create["resulting_artifact"] == "initiative:1"


def test_failed_login_is_audited(client: TestClient, login) -> None:  # noqa: ANN001
    client.post("/auth/login", json={"username": "demo_analyst", "password": "bad"})
    events = client.get("/audit", headers=login("security")).json()
    assert any(e["action"] == "auth.login" and e["decision"] == "denied" for e in events)


def test_chain_verifies_when_untouched(client: TestClient, login) -> None:  # noqa: ANN001
    _create(client, login("analyst"))
    r = client.get("/audit/verify", headers=login("security")).json()
    assert r == {"intact": True, "first_tampered_id": None}


def test_chain_detects_tampering(client: TestClient, login) -> None:  # noqa: ANN001
    _create(client, login("analyst"))
    with engine.begin() as conn:
        conn.execute(text("UPDATE audit_events SET decision='forged' WHERE action='auth.login'"))
    r = client.get("/audit/verify", headers=login("security")).json()
    assert r["intact"] is False
    assert r["first_tampered_id"] is not None
