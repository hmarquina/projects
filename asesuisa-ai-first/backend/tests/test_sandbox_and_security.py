import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from app.ai.artifact_generators import derive_acceptance, derive_api_contract
from app.pipeline import codegen, evidence, sandbox, security_checks, testgen
from tests.helpers import GOOD


def _files() -> dict[str, str]:
    payload = json.dumps(
        {
            "openapi": derive_api_contract(GOOD).openapi,
            "criteria": [c.model_dump() for c in derive_acceptance(GOOD).criteria],
        }
    )
    return {**codegen.generate(payload).files, **testgen.generate(payload).files}


# ---------- sandbox ----------
def test_generated_suite_passes_in_sandbox() -> None:
    res = sandbox.run_tests(_files())
    assert res["ok"] and len(res["tests"]) >= 10
    assert {t["outcome"] for t in res["tests"]} == {"passed"}


def test_defective_service_is_caught_by_generated_tests() -> None:
    """Mutación: si el servicio deja de aplicar la autorización, las pruebas deben fallar."""
    files = _files()
    files["generated_service/app.py"] = files["generated_service/app.py"].replace(
        'raise HTTPException(403, "Permiso insuficiente")', "pass"
    )
    res = sandbox.run_tests(files)
    assert not res["ok"]
    assert any(t["outcome"] == "failed" and "forbidden" in t["name"] for t in res["tests"])


def test_contract_conformance_catches_undeclared_status() -> None:
    files = _files()
    files["generated_service/app.py"] = files["generated_service/app.py"].replace(
        'JSONResponse({"detail": "Datos inválidos"}, status_code=400)',
        'JSONResponse({"detail": "Datos inválidos"}, status_code=418)',
    )
    assert not sandbox.run_tests(files)["ok"]


def test_sandbox_timeout_is_a_failure() -> None:
    files = {"tests/test_loop.py": "def test_x():\n    while True:\n        pass\n"}
    res = sandbox.run_tests(files, timeout=3)
    assert not res["ok"] and "timeout" in res["reason"]


def test_sandbox_without_results_fails_closed() -> None:
    res = sandbox.run_tests({"tests/test_syntax.py": "def test_x(:\n"})
    assert res["ok"] is False


def test_sandbox_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        sandbox.materialize(tmp_path, {"../escape.py": "x = 1"})


def test_sandbox_does_not_expose_platform_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_SECRET_FOR_TEST", "no-debe-verse")
    files = {
        "tests/test_env.py": (
            "from os import environ\n\n\ndef test_isolated():\n"
            "    assert 'PLATFORM_SECRET_FOR_TEST' not in environ\n"
            "    assert 'DATABASE_URL' not in environ\n"
        )
    }
    assert sandbox.run_tests(files)["ok"]


# ---------- secretos ----------
@pytest.mark.parametrize(
    "content",
    [
        "-----BEGIN RSA PRIVATE KEY-----",
        "k = 'AKIAABCDEFGHIJKLMNOP'",
        "password = 'supersecreto123'",
        'API_KEY = "abcdefgh12345678"',
    ],
)
def test_secret_scanner_detects_literals(content: str) -> None:
    files = {"generated_service/app.py": "from os import environ\n" + content}
    res = security_checks.scan_secrets(files)
    assert res["ok"] is False and res["findings"]


def test_generated_service_reads_secret_from_environment() -> None:
    res = security_checks.scan_secrets(_files())
    assert res["ok"] and res["env_sourced"]


def test_scanner_requires_env_usage() -> None:
    assert not security_checks.scan_secrets({"generated_service/app.py": "x = 1"})["ok"]


# ---------- SAST ----------
def test_bandit_passes_generated_code() -> None:
    res = security_checks.run_bandit(_files())
    assert res["status"] == "passed" and res["high"] == 0 and res["medium"] == 0


def test_bandit_blocks_insecure_code() -> None:
    res = security_checks.run_bandit(
        {"x.py": "import pickle\n\ndef f(b):\n    return pickle.loads(b)\n"}
    )
    assert res["status"] == "failed" and res["medium"] + res["high"] >= 1


# ---------- dependencias ----------
def test_unknown_dependency_is_blocked() -> None:
    res = security_checks.check_dependencies("fastapi>=0.1\nevil-package==1.0\n", audit=False)
    assert res["status"] == "failed" and "evil-package" in res["reason"]


def test_disabled_audit_is_skipped_not_passed() -> None:
    res = security_checks.check_dependencies(codegen.REQUIREMENTS, audit=False)
    assert res["status"] == "skipped"


def _fake_run(stdout: str = "", raises: Exception | None = None) -> Any:
    def run(*_a: Any, **_k: Any) -> Any:
        if raises:
            raise raises
        return subprocess.CompletedProcess([], 0, stdout, "")

    return run


def test_pip_audit_vulnerability_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    out = json.dumps({"dependencies": [{"name": "fastapi", "vulns": [{"id": "PYSEC-1"}]}]})
    monkeypatch.setattr(security_checks.subprocess, "run", _fake_run(out))
    res = security_checks.check_dependencies(codegen.REQUIREMENTS, audit=True)
    assert res["status"] == "failed" and res["vulnerabilities"] == 1


def test_pip_audit_clean_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security_checks.subprocess, "run", _fake_run(json.dumps({"dependencies": [{"vulns": []}]}))
    )
    assert (
        security_checks.check_dependencies(codegen.REQUIREMENTS, audit=True)["status"] == "passed"
    )


def test_pip_audit_unavailable_is_skipped_not_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    err = subprocess.TimeoutExpired("pip-audit", 1)
    monkeypatch.setattr(security_checks.subprocess, "run", _fake_run(raises=err))
    res = security_checks.check_dependencies(codegen.REQUIREMENTS, audit=True)
    assert res["status"] == "skipped" and "NO verificado" in res["reason"]


# ---------- evidencia y readiness ----------
def test_traceability_reflects_real_results() -> None:
    mapping = [
        {"ac_id": "A", "tests": ["t1", "t2"], "kind": "verified", "reason": ""},
        {"ac_id": "B", "tests": ["t3"], "kind": "smoke", "reason": ""},
        {"ac_id": "C", "tests": [], "kind": "manual", "reason": "operativo"},
        {"ac_id": "D", "tests": ["t_missing"], "kind": "verified", "reason": ""},
    ]
    tests = [{"name": "t1", "outcome": "passed"}, {"name": "t2", "outcome": "failed"},
             {"name": "t3", "outcome": "passed"}]  # fmt: skip
    got = {r["ac_id"]: r["status"] for r in evidence.traceability(mapping, tests)}
    assert got == {"A": "failed", "B": "smoke", "C": "manual", "D": "failed"}


def _ready(deps_status: str) -> dict[str, Any]:
    tests = [{"name": "t", "outcome": "passed"}]
    from app.pipeline.docs import REQUIRED_SECTIONS

    return evidence.readiness(
        analysis_score=100, tests=tests, bandit={"status": "passed"}, secrets={"ok": True},
        deps={"status": deps_status, "reason": "sin red"},
        trace=[{"ac_id": "A", "status": "verified"}], readme="\n".join(REQUIRED_SECTIONS),
        evidence_complete=True,
    )  # fmt: skip


def test_skipped_dependency_audit_lowers_score_and_is_listed() -> None:
    ok, skipped = _ready("passed"), _ready("skipped")
    assert ok["score"] - skipped["score"] == 8
    assert any("dependencias" in u for u in skipped["unverified"])
    assert ok["score"] == 100


@pytest.mark.skipif(
    os.environ.get("RUN_ONLINE_TESTS") != "1", reason="requiere red (RUN_ONLINE_TESTS=1)"
)
def test_real_pip_audit_on_generated_requirements() -> None:
    res = security_checks.check_dependencies(codegen.REQUIREMENTS, audit=True, timeout=180)
    assert res["status"] in {"passed", "failed"}, res  # con red NO debe quedar en skipped
