"""Levanta la demo con un solo comando, en Windows, Linux y macOS, y desde cualquier carpeta.

    python scripts/demo.py                 # prepara lo que falte, siembra los usuarios y arranca
    python scripts/demo.py --port 9000     # otro puerto (por defecto 8765)
    python scripts/demo.py --no-ui         # sin compilar la interfaz (no requiere Node)
    python scripts/demo.py --reset         # borra la base y las credenciales locales y empieza de cero
    python scripts/demo.py --dry-run       # muestra los pasos sin ejecutarlos

Hace: crea .venv, instala dependencias, compila la UI, siembra usuarios demo y arranca el servidor.
La contrasena demo y el secreto JWT se generan una vez y se guardan en backend/data/demo.env
(carpeta ignorada por git). Solo usa caracteres que una consola de Windows puede mostrar.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import shutil
import subprocess  # nosec B404 - se invocan solo pip, npm y el propio Python, sin shell
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = ROOT / ".venv"
STATE = BACKEND / "data" / "demo.env"
DB_FILE = BACKEND / "data" / "demo.db"
DEFAULT_PORT = 8765
USERS = ("analyst", "tech_lead", "approver", "security", "viewer", "admin")


def venv_python(windows: bool | None = None) -> Path:
    """Intérprete del entorno virtual: `Scripts/python.exe` en Windows (también en Git Bash), `bin/python` en el resto."""
    is_windows = os.name == "nt" if windows is None else windows
    return VENV / ("Scripts/python.exe" if is_windows else "bin/python")


def read_state(path: Path = STATE) -> dict[str, str]:
    if not path.exists():
        return {}
    pairs = (
        line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line
    )
    return {k.strip(): v.strip() for k, v in pairs}


def ensure_state(
    environ: dict[str, str], path: Path = STATE, db_file: Path = DB_FILE
) -> dict[str, str]:
    """Contrasena y secreto: los da el entorno o se generan una vez y se reutilizan."""
    state = read_state(path)
    wanted = environ.get("DEMO_PASSWORD")
    if wanted is not None:
        if len(wanted) < 12:
            raise SystemExit("DEMO_PASSWORD debe tener al menos 12 caracteres.")
        if state.get("DEMO_PASSWORD") not in (None, wanted) and db_file.exists():
            raise SystemExit(
                "La base de datos ya existe con otra contrasena. Usa --reset para empezar de cero "
                "o quita la variable DEMO_PASSWORD."
            )
        state["DEMO_PASSWORD"] = wanted
    state.setdefault("DEMO_PASSWORD", secrets.token_urlsafe(12))
    state["JWT_SECRET"] = (
        environ.get("JWT_SECRET") or state.get("JWT_SECRET") or secrets.token_hex(32)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{k}={v}\n" for k, v in state.items()), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:  # Windows: los permisos POSIX no aplican
        pass
    return state


def build_env(base: dict[str, str], state: dict[str, str], port: int) -> dict[str, str]:
    env = dict(base)
    env.update(
        DEMO_PASSWORD=state["DEMO_PASSWORD"],
        JWT_SECRET=state["JWT_SECRET"],
        APP_PORT=str(port),
        PYTHONUTF8="1",
    )
    env.setdefault("DATABASE_URL", "sqlite:///./data/demo.db")  # relativo a backend/
    env.setdefault(
        "PIPELINE_DEPENDENCY_AUDIT", "false"
    )  # sin red: queda "no verificado", nunca "paso"
    return env


def requirements_hash() -> str:
    data = (BACKEND / "requirements.txt").read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


Step = tuple[str, list[str], Path]


def plan(args: argparse.Namespace, npm: str | None) -> list[Step]:
    py = str(venv_python())
    steps: list[Step] = []
    if not venv_python().exists():
        steps.append(
            ("Crear el entorno virtual (.venv)", [sys.executable, "-m", "venv", str(VENV)], ROOT)
        )
    stamp = VENV / ".deps-stamp"
    if not stamp.exists() or stamp.read_text().strip() != requirements_hash():
        steps.append(
            (
                "Instalar dependencias de Python",
                [py, "-m", "pip", "install", "-r", "requirements.txt"],
                BACKEND,
            )
        )
    if not args.no_ui:
        if npm is None:
            print(
                "AVISO: no se encontro Node/npm. La API funcionara, pero sin interfaz. Instala Node 18+ o usa --no-ui."
            )
        elif args.rebuild_ui or not (FRONTEND / "dist" / "index.html").exists():
            steps.append(
                (
                    "Instalar dependencias de la interfaz",
                    [npm, "ci", "--no-audit", "--no-fund"],
                    FRONTEND,
                )
            )
            steps.append(("Compilar la interfaz", [npm, "run", "build"], FRONTEND))
    steps.append(("Sembrar los usuarios demo", [py, "-m", "app.seed"], BACKEND))
    return steps


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=cwd, env=env, check=True)  # noqa: S603  # nosec B603


def reset() -> None:
    for path in (DB_FILE, STATE):
        if path.exists():
            path.unlink()
            print(f"Eliminado: {path.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Levanta la demo de la Control Tower con un solo comando."
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("APP_PORT", DEFAULT_PORT)))
    parser.add_argument(
        "--no-ui", action="store_true", help="no compilar la interfaz (no requiere Node)"
    )
    parser.add_argument(
        "--rebuild-ui", action="store_true", help="recompilar la interfaz aunque ya exista"
    )
    parser.add_argument(
        "--reset", action="store_true", help="borrar la base y las credenciales locales"
    )
    parser.add_argument("--dry-run", action="store_true", help="mostrar los pasos sin ejecutarlos")
    args = parser.parse_args(argv)

    if sys.version_info < (3, 10):  # noqa: UP036 - aviso claro para quien tenga 3.9
        print(f"Se requiere Python 3.10 o superior (tienes {sys.version.split()[0]}).")
        return 1
    if not 1 <= args.port <= 65535:
        print("El puerto debe estar entre 1 y 65535.")
        return 1
    if args.reset and not args.dry_run:
        reset()

    npm = None if args.no_ui else shutil.which("npm")
    state = (
        ensure_state(dict(os.environ))
        if not args.dry_run
        else {"DEMO_PASSWORD": "(se genera)", "JWT_SECRET": "x"}
    )
    env = build_env(dict(os.environ), state, args.port)
    steps = plan(args, npm)

    try:
        for description, cmd, cwd in steps:
            print(f"\n== {description}")
            print("   " + " ".join(cmd))
            if not args.dry_run:
                run(cmd, cwd, env)
        if not args.dry_run and any(
            d.startswith("Instalar dependencias de Python") for d, _, _ in steps
        ):
            (VENV / ".deps-stamp").write_text(requirements_hash(), encoding="utf-8")

        if not args.no_ui and not args.dry_run and not (FRONTEND / "dist" / "index.html").exists():
            print("\nAVISO: no existe frontend/dist/index.html; la pagina mostrara un aviso en vez de la UI.")
        url = f"http://127.0.0.1:{args.port}"
        print(f"\n== Control Tower en {url}")
        print(f"   Usuarios: {', '.join('demo_' + u for u in USERS)}")
        print(f"   Contrasena (la misma para todos): {state['DEMO_PASSWORD']}")
        print("   Ctrl+C para detener.\n")
        if args.dry_run:
            return 0
        run([str(venv_python()), "-m", "app"], BACKEND, env)
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    except subprocess.CalledProcessError as exc:
        print(f"\nFallo el paso: {' '.join(str(c) for c in exc.cmd)} (codigo {exc.returncode})")
        return exc.returncode or 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
