"""Regresión de portabilidad: Python 3.10 y Windows (entorno real de un usuario)."""

import ast
import json
from pathlib import Path

import pytest

from app.ai.artifact_generators import derive_acceptance, derive_api_contract
from app.db import make_engine
from app.pipeline import codegen, sandbox, testgen
from tests.helpers import GOOD

APP = Path(__file__).resolve().parents[1] / "app"


def _imports_datetime_utc(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module == "datetime":
            if any(alias.name == "UTC" for alias in node.names):
                return True
    return False


def test_application_code_does_not_use_datetime_utc() -> None:
    """`datetime.UTC` existe solo desde Python 3.11; el proyecto soporta 3.10."""
    offenders = [
        str(p.relative_to(APP)) for p in APP.rglob("*.py") if _imports_datetime_utc(p.read_text())
    ]
    assert offenders == []


def test_application_syntax_is_valid_for_python_310() -> None:
    for path in APP.rglob("*.py"):
        ast.parse(path.read_text(), feature_version=(3, 10))


def test_generated_service_is_python_310_compatible() -> None:
    """El servicio generado corre en el mismo intérprete que la plataforma."""
    payload = json.dumps(
        {
            "openapi": derive_api_contract(GOOD).openapi,
            "criteria": [c.model_dump() for c in derive_acceptance(GOOD).criteria],
        }
    )
    for source in {**codegen.generate(payload).files, **testgen.generate(payload).files}.values():
        if source.strip().startswith(("import", "from", '"""')):
            ast.parse(source, feature_version=(3, 10))
            assert not _imports_datetime_utc(source)


def test_sandbox_runs_without_posix_resource_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """En Windows no existe `resource`: el sandbox debe seguir funcionando (con menos aislamiento)."""
    monkeypatch.setattr(sandbox, "_HAS_RLIMIT", False)
    files = {"tests/test_ok.py": "def test_ok():\n    assert True\n"}
    res = sandbox.run_tests(files)
    assert res["ok"] and [t["outcome"] for t in res["tests"]] == ["passed"]


def test_sandbox_env_passes_systemroot_only_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYSTEMROOT", "C:\\Windows")
    monkeypatch.setenv("PLATFORM_SECRET_FOR_TEST", "no-debe-verse")
    win = sandbox.build_env("tmp", Path("r.json"), windows=True)
    posix = sandbox.build_env("tmp", Path("r.json"), windows=False)
    assert win["SYSTEMROOT"] == "C:\\Windows" and "SYSTEMROOT" not in posix
    for env in (win, posix):  # nunca se filtran variables de la plataforma
        assert "PLATFORM_SECRET_FOR_TEST" not in env and "DATABASE_URL" not in env


def test_sqlite_creates_missing_data_directory(tmp_path: Path) -> None:
    """Un clon nuevo no tiene `backend/data/`; antes fallaba con 'unable to open database file'."""
    db_file = tmp_path / "nueva" / "carpeta" / "app.db"
    engine = make_engine(f"sqlite:///{db_file}")
    with engine.connect():
        pass
    assert db_file.parent.is_dir()
