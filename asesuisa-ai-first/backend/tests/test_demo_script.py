"""El lanzador de un solo comando (scripts/demo.py) debe ser robusto y multiplataforma."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("demo", ROOT / "scripts" / "demo.py")
assert SPEC and SPEC.loader
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


def test_venv_python_path_by_platform() -> None:
    """Git Bash en Windows usa Scripts/, no bin/ (el error real de un usuario)."""
    assert demo.venv_python(windows=True).parts[-2:] == ("Scripts", "python.exe")
    assert demo.venv_python(windows=False).parts[-2:] == ("bin", "python")


def test_script_only_uses_characters_a_windows_console_can_print() -> None:
    """Flechas, vinetas o emojis romperian `print` en consolas cp1252."""
    (ROOT / "scripts" / "demo.py").read_text(encoding="utf-8").encode("cp1252")


def test_project_root_does_not_depend_on_the_current_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El usuario ejecuto desde backend/ y los comandos relativos fallaron."""
    monkeypatch.chdir(ROOT / "backend")
    assert demo.ROOT == ROOT and demo.BACKEND == ROOT / "backend"
    assert demo.requirements_hash()


def test_state_is_generated_once_and_reused(tmp_path: Path) -> None:
    path, db = tmp_path / "data" / "demo.env", tmp_path / "demo.db"
    first = demo.ensure_state({}, path, db)
    assert len(first["DEMO_PASSWORD"]) >= 12 and len(first["JWT_SECRET"]) == 64
    assert demo.ensure_state({}, path, db) == first
    assert path.read_text().count("DEMO_PASSWORD=") == 1


def test_environment_overrides_are_respected(tmp_path: Path) -> None:
    state = demo.ensure_state(
        {"DEMO_PASSWORD": "contrasena-propia-123", "JWT_SECRET": "s" * 40},
        tmp_path / "e",
        tmp_path / "d",
    )
    assert state["DEMO_PASSWORD"] == "contrasena-propia-123" and state["JWT_SECRET"] == "s" * 40


def test_short_password_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="12 caracteres"):
        demo.ensure_state({"DEMO_PASSWORD": "corta"}, tmp_path / "e", tmp_path / "d")


def test_changing_password_with_an_existing_database_requires_reset(tmp_path: Path) -> None:
    path, db = tmp_path / "e", tmp_path / "demo.db"
    demo.ensure_state({"DEMO_PASSWORD": "primera-contrasena-1"}, path, db)
    db.write_text("existe")
    with pytest.raises(SystemExit, match="--reset"):
        demo.ensure_state({"DEMO_PASSWORD": "otra-contrasena-123"}, path, db)


def test_environment_for_children_has_safe_defaults() -> None:
    env = demo.build_env({"PATH": "x"}, {"DEMO_PASSWORD": "p" * 12, "JWT_SECRET": "s" * 64}, 9100)
    assert env["APP_PORT"] == "9100" and env["DATABASE_URL"] == "sqlite:///./data/demo.db"
    assert env["PIPELINE_DEPENDENCY_AUDIT"] == "false"  # sin red: "no verificado", nunca "paso"
    assert (
        demo.build_env(
            {"DATABASE_URL": "sqlite:///otra.db"}, {"DEMO_PASSWORD": "p" * 12, "JWT_SECRET": "s"}, 1
        )["DATABASE_URL"]
        == "sqlite:///otra.db"
    )


def test_dry_run_executes_nothing_and_lists_the_steps(capsys: pytest.CaptureFixture[str]) -> None:
    assert demo.main(["--dry-run", "--no-ui", "--port", "9200"]) == 0
    out = capsys.readouterr().out
    assert "Sembrar los usuarios demo" in out and "http://127.0.0.1:9200" in out
    assert "(se genera)" in out  # no crea credenciales en un dry-run


@pytest.mark.parametrize("port", ["0", "70000"])
def test_invalid_port_is_rejected(port: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert demo.main(["--dry-run", "--port", port]) == 1
    assert "entre 1 y 65535" in capsys.readouterr().out
