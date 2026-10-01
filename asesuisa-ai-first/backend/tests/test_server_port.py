import pytest
from pydantic import ValidationError

from app import __main__ as launcher
from app.config import Settings


def test_default_port_is_not_8000(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_PORT", raising=False)
    monkeypatch.delenv("APP_HOST", raising=False)
    s = Settings(_env_file=None)
    assert s.app_port == 8765 != 8000
    assert s.app_host == "127.0.0.1"  # solo local por defecto: no se expone a la red


def test_port_is_configurable_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_PORT", "9123")
    assert Settings(_env_file=None).app_port == 9123


@pytest.mark.parametrize("bad", ["0", "-1", "65536", "99999", "abc", ""])
def test_invalid_ports_are_rejected(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setenv("APP_PORT", bad)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_launcher_uses_the_configured_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_PORT", "9456")
    monkeypatch.delenv("APP_HOST", raising=False)
    launcher.get_settings.cache_clear()
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *a, **k: calls.append((a, k)))
    try:
        launcher.main()
    finally:
        launcher.get_settings.cache_clear()
    assert calls == [(("app.main:app",), {"host": "127.0.0.1", "port": 9456})]
