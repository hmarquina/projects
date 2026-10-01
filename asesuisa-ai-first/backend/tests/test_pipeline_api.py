import hashlib
import io
import json
import zipfile

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.ai.gateway import ModelGateway, get_gateway
from app.db import engine
from app.main import app
from app.pipeline import release
from tests.helpers import Tampering, ready_initiative, run_pipeline


def _override(transform) -> None:  # noqa: ANN001
    app.dependency_overrides[get_gateway] = lambda: ModelGateway([Tampering(transform)], {"mock"})


def _step(run: dict, name: str) -> dict:  # noqa: ANN001
    return next(s for s in run["steps"] if s["name"] == name)


def test_pipeline_happy_path_awaits_approval(client: TestClient, login) -> None:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    assert run["status"] == "awaiting_approval"
    assert run["readiness"]["score"] >= 85
    assert _step(run, "dependencias")["status"] == "skipped"  # offline en tests: no se finge
    assert any("AC-SR-2" in u for u in run["readiness"]["unverified"])
    assert "docs/README.md" in run["files"] and "tests/test_api.py" in run["files"]


def test_pipeline_requires_all_current_artifacts(client: TestClient, login) -> None:  # noqa: ANN001
    a = login("analyst")
    r = client.post(
        "/initiatives", json={"title": "Reclamos", "description": ready_text()}, headers=a
    )
    iid = r.json()["id"]
    client.post(f"/initiatives/{iid}/analyze", headers=a)
    client.post(f"/initiatives/{iid}/artifacts/stories", headers=a)
    r = client.post(f"/initiatives/{iid}/pipeline", headers=login("tech_lead"))
    assert r.status_code == 409 and "Falta el artefacto" in r.json()["detail"]


def ready_text() -> str:
    from tests.helpers import GOOD

    return GOOD


def test_pipeline_blocked_after_requirement_changes(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    client.patch(
        f"/initiatives/{iid}",
        json={"description": ready_text() + " Otro."},
        headers=login("analyst"),
    )
    assert (
        client.post(f"/initiatives/{iid}/pipeline", headers=login("tech_lead")).status_code == 409
    )


def test_pipeline_rbac(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    url = f"/initiatives/{iid}/pipeline"
    for role in ("viewer", "analyst", "approver", "security"):
        assert client.post(url, headers=login(role)).status_code == 403, role
    assert client.post(url).status_code == 401


def test_malicious_generated_code_is_never_executed(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    _override(lambda src: "import subprocess\nsubprocess.run(['touch','/tmp/pwned'])\n" + src)
    run = run_pipeline(client, login, iid)
    assert run["status"] == "blocked"
    assert _step(run, "politica_estatica")["status"] == "failed"
    assert "subprocess" in _step(run, "politica_estatica")["detail"]
    assert _step(run, "pruebas")["status"] == "skipped"
    assert _step(run, "sast_bandit")["status"] == "skipped"


def test_defective_generated_code_is_blocked_by_tests(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    _override(lambda src: src.replace('raise HTTPException(403, "Permiso insuficiente")', "pass"))
    run = run_pipeline(client, login, iid)
    assert run["status"] == "blocked" and _step(run, "pruebas")["status"] == "failed"
    assert any(r["status"] == "failed" for r in run["traceability"])


def test_hardcoded_secret_in_generated_code_blocks(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    _override(lambda src: src + "\nsecret = 'abcdefgh12345678'\n")
    run = run_pipeline(client, login, iid)
    assert run["status"] == "blocked" and _step(run, "escaneo_secretos")["status"] == "failed"


def test_insecure_pattern_blocked_by_sast(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    _override(lambda src: src + "\nURL = 'http://0.0.0.0'\nTOKEN_URL = '0.0.0.0'\n")
    run = run_pipeline(client, login, iid)
    # B104 (bind a todas las interfaces) es MEDIUM: debe bloquear
    assert run["status"] == "blocked" and _step(run, "sast_bandit")["status"] == "failed"


def test_approval_flow_and_segregation(client: TestClient, login) -> None:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    url = f"/pipeline-runs/{run['id']}/decision"
    ok = {"decision": "approved", "comment": "Revisado el reporte", "risk_acknowledged": True}
    assert (
        client.post(url, json=ok, headers=login("tech_lead")).status_code == 403
    )  # no tiene permiso
    assert client.post(url, json=ok, headers=login("analyst")).status_code == 403
    assert (
        client.post(
            url, json={**ok, "risk_acknowledged": False}, headers=login("approver")
        ).status_code
        == 422
    )
    assert (
        client.post(url, json={**ok, "comment": "ok"}, headers=login("approver")).status_code == 422
    )
    done = client.post(url, json=ok, headers=login("approver"))
    assert done.status_code == 200 and done.json()["approval"]["approver"] == "demo_approver"
    assert client.post(url, json=ok, headers=login("approver")).status_code == 409  # ya decidido


def test_contributor_cannot_approve_own_work(client: TestClient, login) -> None:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    with engine.begin() as conn:  # simula que el aprobador participó en el trabajo
        conn.execute(
            text("UPDATE pipeline_runs SET contributors=:c WHERE id=:i"),
            {"c": json.dumps(["demo_analyst", "demo_approver"]), "i": run["id"]},
        )
    body = {"decision": "approved", "comment": "Revisado el reporte", "risk_acknowledged": True}
    r = client.post(f"/pipeline-runs/{run['id']}/decision", json=body, headers=login("approver"))
    assert r.status_code == 403 and "Segregación" in r.json()["detail"]


def test_blocked_run_cannot_be_decided_or_released(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    _override(lambda src: "import socket\n" + src)
    run = run_pipeline(client, login, iid)
    body = {"decision": "approved", "comment": "Revisado el reporte", "risk_acknowledged": True}
    assert (
        client.post(
            f"/pipeline-runs/{run['id']}/decision", json=body, headers=login("approver")
        ).status_code
        == 409
    )
    assert (
        client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead")).status_code
        == 409
    )


def test_rejection_is_recorded_and_blocks_release(client: TestClient, login) -> None:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    body = {"decision": "rejected", "comment": "Falta verificar disponibilidad"}
    r = client.post(f"/pipeline-runs/{run['id']}/decision", json=body, headers=login("approver"))
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert (
        client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead")).status_code
        == 409
    )


def _approved(client: TestClient, login) -> dict:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    body = {"decision": "approved", "comment": "Revisado el reporte", "risk_acknowledged": True}
    assert (
        client.post(
            f"/pipeline-runs/{run['id']}/decision", json=body, headers=login("approver")
        ).status_code
        == 200
    )
    return run


def test_release_requires_approval_and_is_single(client: TestClient, login) -> None:  # noqa: ANN001
    run = run_pipeline(client, login, ready_initiative(client, login))
    assert (
        client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead")).status_code
        == 409
    )
    run = _approved(client, login)
    assert (
        client.post(f"/pipeline-runs/{run['id']}/release", headers=login("approver")).status_code
        == 403
    )
    first = client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead"))
    assert first.status_code == 201 and first.json()["version"] == "v1"
    assert (
        client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead")).status_code
        == 409
    )


def test_release_package_is_verifiable(client: TestClient, login) -> None:  # noqa: ANN001
    run = _approved(client, login)
    rel = client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead")).json()
    dl = client.get(f"/releases/{rel['id']}/download", headers=login("viewer"))
    assert dl.status_code == 200 and dl.headers["content-type"] == "application/zip"
    assert (
        hashlib.sha256(dl.content).hexdigest()
        == rel["package_sha256"]
        == dl.headers["x-package-sha256"]
    )
    zf = zipfile.ZipFile(io.BytesIO(dl.content))
    manifest = json.loads(zf.read("MANIFEST.json"))
    assert manifest["approved_by"] == "demo_approver" and manifest["readiness"] >= 85
    for path, digest in manifest["files"].items():
        assert hashlib.sha256(zf.read(path)).hexdigest() == digest, path
    evidence = json.loads(zf.read("evidence.json"))
    assert evidence["approval"]["approver"] == "demo_approver"
    assert evidence["requirement_ref"].startswith("sha256:") and evidence["ai_artifacts"]


def test_release_detects_tampered_files(client: TestClient, login) -> None:  # noqa: ANN001
    run = _approved(client, login)
    with engine.begin() as conn:
        raw = conn.execute(
            text("SELECT files_json FROM pipeline_runs WHERE id=:i"), {"i": run["id"]}
        ).scalar_one()
        files = json.loads(raw)
        files["generated_service/app.py"] += "\n# manipulado"
        conn.execute(text("UPDATE pipeline_runs SET files_json=:f WHERE id=:i"),
                     {"f": json.dumps(files), "i": run["id"]})  # fmt: skip
    r = client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead"))
    assert r.status_code == 409 and "Integridad" in r.json()["detail"]


def test_package_build_is_deterministic() -> None:
    files, manifest = {"b.txt": "2", "a.txt": "1"}, {"release": "v1"}
    assert release.build_package(files, manifest) == release.build_package(
        dict(reversed(files.items())), manifest
    )


def test_full_audit_trail_for_pipeline(client: TestClient, login) -> None:  # noqa: ANN001
    run = _approved(client, login)
    client.post(f"/pipeline-runs/{run['id']}/release", headers=login("tech_lead"))
    events = client.get("/audit?limit=100", headers=login("security")).json()
    by_action = {e["action"]: e for e in events}
    assert by_action["pipeline.run"]["ai_model"] == "mock-heuristic-1"
    assert by_action["pipeline.run"]["prompt_version"].startswith("code_skeleton@1.0.0+")
    assert by_action["pipeline.decision"]["approval"] == "approved:demo_approver"
    assert by_action["release.create"]["resulting_artifact"].startswith("release:")
    assert by_action["release.create"]["output_ref"].startswith("sha256:")
    assert client.get("/audit/verify", headers=login("security")).json()["intact"] is True


def test_file_and_run_endpoints(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    run = run_pipeline(client, login, iid)
    v = login("viewer")
    assert client.get(f"/pipeline-runs/{run['id']}", headers=v).json()["id"] == run["id"]
    assert len(client.get(f"/initiatives/{iid}/pipeline-runs", headers=v).json()) == 1
    f = client.get(f"/pipeline-runs/{run['id']}/files/docs/README.md", headers=v)
    assert f.status_code == 200 and "## Criterios de aceptación y cobertura" in f.text
    assert client.get(f"/pipeline-runs/{run['id']}/files/nada.py", headers=v).status_code == 404
    assert client.get("/pipeline-runs/999", headers=v).status_code == 404
    assert client.get("/releases/999", headers=v).status_code == 404


def test_global_listings_and_evidence(client: TestClient, login) -> None:  # noqa: ANN001
    iid = ready_initiative(client, login)
    run = run_pipeline(client, login, iid)
    v = login("viewer")
    assert run["evidence"]["tests"]["failed"] == 0 and "bandit" in run["evidence"]["security"]
    assert [r["id"] for r in client.get("/pipeline-runs", headers=v).json()] == [run["id"]]
    pending = client.get("/pipeline-runs?status=awaiting_approval", headers=v).json()
    assert len(pending) == 1
    assert client.get("/pipeline-runs?status=approved", headers=v).json() == []
    assert client.get("/pipeline-runs?status=nope", headers=v).status_code == 422
    assert client.get("/releases", headers=v).json() == []
    assert client.get("/pipeline-runs").status_code == 401
