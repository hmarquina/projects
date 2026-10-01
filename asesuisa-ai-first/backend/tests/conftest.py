import os
import tempfile
from collections.abc import Iterator

# Debe fijarse antes de importar la app (el engine se crea al importar).
_tmp = tempfile.mkdtemp()
# TEST_DATABASE_URL permite correr toda la suite contra PostgreSQL (ver scripts/test_postgres.py).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_tmp}/test.db"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
os.environ["DEMO_PASSWORD"] = "synthetic-demo-pass-123"
os.environ["PIPELINE_DEPENDENCY_AUDIT"] = "false"  # tests offline; hay un test dedicado

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_users  # noqa: E402

PASSWORD = os.environ["DEMO_PASSWORD"]


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_users(db, PASSWORD)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def login(client: TestClient):  # noqa: ANN201
    def _login(role: str) -> dict[str, str]:
        r = client.post("/auth/login", json={"username": f"demo_{role}", "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login
