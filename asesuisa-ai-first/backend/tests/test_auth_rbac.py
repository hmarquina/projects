import jwt
from fastapi.testclient import TestClient

from app.config import get_settings


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_login_wrong_password_denied(client: TestClient) -> None:
    r = client.post("/auth/login", json={"username": "demo_analyst", "password": "nope"})
    assert r.status_code == 401


def test_login_unknown_user_denied(client: TestClient) -> None:
    r = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert r.status_code == 401


def test_endpoint_requires_token(client: TestClient) -> None:
    assert client.get("/initiatives").status_code == 401


def test_garbage_token_rejected(client: TestClient) -> None:
    r = client.get("/initiatives", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_token_signed_with_other_secret_rejected(client: TestClient) -> None:
    forged = jwt.encode(
        {"sub": "demo_admin", "role": "admin", "iss": get_settings().jwt_issuer,
         "exp": 9999999999},
        "z" * 40, algorithm="HS256",
    )  # fmt: skip
    r = client.get("/audit", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_alg_none_token_rejected(client: TestClient) -> None:
    forged = jwt.encode(
        {"sub": "x", "role": "admin", "iss": get_settings().jwt_issuer, "exp": 9999999999},
        key=None, algorithm="none",
    )  # fmt: skip
    r = client.get("/audit", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


def test_viewer_cannot_create_initiative(client: TestClient, login) -> None:  # noqa: ANN001
    r = client.post("/initiatives", json={"title": "Reclamos"}, headers=login("viewer"))
    assert r.status_code == 403


def test_approver_cannot_create_initiative(client: TestClient, login) -> None:  # noqa: ANN001
    """Segregación de funciones: quien aprueba no genera."""
    r = client.post("/initiatives", json={"title": "Reclamos"}, headers=login("approver"))
    assert r.status_code == 403


def test_analyst_cannot_read_audit(client: TestClient, login) -> None:  # noqa: ANN001
    assert client.get("/audit", headers=login("analyst")).status_code == 403
