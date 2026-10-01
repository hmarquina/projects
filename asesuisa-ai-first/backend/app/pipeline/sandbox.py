"""Ejecución de las pruebas generadas en un directorio temporal aislado.

Aislamiento de proceso: `python -I`, entorno mínimo (sin secretos de la plataforma), límites de
CPU/memoria/archivos y timeout. NO es un sandbox de contenedor: en producción debe ejecutarse en
un runner efímero sin red (p. ej. contenedor/gVisor). La política estática corre antes.
"""

import json
import os
import secrets

# ejecución controlada del intérprete propio, sin shell
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path
from typing import Any

try:  # `resource` no existe en Windows: allí no hay límites de proceso (aislamiento más débil)
    import resource
except ImportError:  # pragma: no cover - solo en Windows
    resource = None  # type: ignore[assignment]

_HAS_RLIMIT = resource is not None

# Harness inyectado por la plataforma (no forma parte del código generado ni pasa por la política).
_HARNESS = """import json
import os

_tests = []


def pytest_runtest_logreport(report):
    ok_phase = report.when == "call" or (report.when == "setup" and not report.passed)
    if ok_phase or (report.when == "teardown" and report.failed):
        _tests.append({"name": report.nodeid.split("::")[-1], "outcome": report.outcome})


def pytest_sessionfinish(session, exitstatus):
    with open(os.environ["PIPELINE_RESULTS"], "w") as fh:
        json.dump({"exitstatus": int(exitstatus), "tests": _tests}, fh)
"""


def _limits() -> None:  # pragma: no cover - corre en el proceso hijo (solo POSIX)
    if resource is None:  # no debería ocurrir: solo se llama si hay `resource`
        return
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (50 * 1024**2, 50 * 1024**2))


def materialize(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = (root / rel).resolve()
        if root.resolve() not in target.parents:  # evita escapes con ../
            raise ValueError(f"Ruta fuera del sandbox: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def build_env(tmp: str, results: Path, windows: bool | None = None) -> dict[str, str]:
    """Entorno mínimo del proceso hijo: sin secretos de la plataforma."""
    is_windows = os.name == "nt" if windows is None else windows
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": tmp,
        "PYTHONHASHSEED": "0",
        "PIPELINE_RESULTS": str(results),
        "JWT_SECRET": secrets.token_hex(32),
    }
    if is_windows:  # Python en Windows no arranca sin SYSTEMROOT
        for key in ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP"):
            if key in os.environ:
                env[key] = os.environ[key]
    return env


def run_tests(files: dict[str, str], timeout: int = 90) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pipeline-") as tmp:
        root = Path(tmp)
        materialize(root, files)
        (root / "conftest.py").write_text(_HARNESS, encoding="utf-8")
        results = root / "results.json"
        env = build_env(tmp, results)
        cmd = [sys.executable, "-I", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--tb=short"]  # fmt: skip
        try:
            proc = subprocess.run(  # noqa: S603  # nosec B603
                cmd,
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=_limits if _HAS_RLIMIT else None,  # noqa: PLW1509
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "reason": f"timeout de {timeout}s", "tests": [], "output": ""}
        if not results.exists():
            return {"ok": False, "reason": "pytest no produjo resultados", "tests": [],
                    "output": (proc.stdout + proc.stderr)[-1500:]}  # fmt: skip
        data = json.loads(results.read_text())
        tests = data["tests"]
        return {
            "ok": data["exitstatus"] == 0 and bool(tests),
            "reason": "" if data["exitstatus"] == 0 else f"pytest exit {data['exitstatus']}",
            "tests": tests,
            "output": "" if data["exitstatus"] == 0 else proc.stdout[-1500:],
        }


__all__ = ["materialize", "run_tests"]
