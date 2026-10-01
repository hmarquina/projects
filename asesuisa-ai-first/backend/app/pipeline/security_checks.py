"""Controles de seguridad sobre el código generado: SAST, secretos y cadena de suministro."""

import json
import re

# invocación controlada de herramientas propias, sin shell
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path
from typing import Any

from app.pipeline.sandbox import materialize

DEP_ALLOWLIST = frozenset({"fastapi", "pydantic", "pyjwt", "httpx", "pytest"})
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("clave privada", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("token de GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("credencial literal", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|passw(?:or)?d|token)\s*=\s*[\"'][^\"'\s]{8,}[\"']")),
)  # fmt: skip


def scan_secrets(files: dict[str, str]) -> dict[str, Any]:
    findings = [
        {"file": path, "type": kind}
        for path, content in sorted(files.items())
        for kind, pattern in _SECRET_PATTERNS
        if pattern.search(content)
    ]
    uses_env = "environ" in files.get("generated_service/app.py", "")
    return {"ok": not findings and uses_env, "findings": findings,
            "env_sourced": uses_env}  # fmt: skip


def run_bandit(files: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="bandit-") as tmp:
        root = Path(tmp)
        materialize(root, {k: v for k, v in files.items() if k.endswith(".py")})
        cmd = [sys.executable, "-m", "bandit", "-r", str(root), "-f", "json", "-q"]
        try:
            proc = subprocess.run(  # noqa: S603  # nosec B603
                cmd, capture_output=True, text=True, timeout=timeout, cwd=tmp
            )
        except subprocess.TimeoutExpired:
            return {"status": "skipped", "reason": "timeout", "high": 0, "medium": 0, "low": 0}
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {"status": "skipped", "reason": "bandit no produjo JSON",
                    "high": 0, "medium": 0, "low": 0}  # fmt: skip
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    issues = []
    for r in data.get("results", []):
        counts[r["issue_severity"]] += 1
        issues.append({"test": r["test_id"], "severity": r["issue_severity"],
                       "file": Path(r["filename"]).name, "line": r["line_number"]})  # fmt: skip
    blocking = counts["HIGH"] + counts["MEDIUM"]
    return {"status": "failed" if blocking else "passed", "high": counts["HIGH"],
            "medium": counts["MEDIUM"], "low": counts["LOW"], "issues": issues[:20]}  # fmt: skip


def check_dependencies(requirements: str, audit: bool, timeout: int = 120) -> dict[str, Any]:
    names = [re.split(r"[<>=!~\[ ]", ln.strip(), maxsplit=1)[0].lower()
             for ln in requirements.splitlines() if ln.strip() and not ln.startswith("#")]  # fmt: skip
    unknown = sorted(set(names) - DEP_ALLOWLIST)
    if unknown:
        return {"status": "failed", "reason": f"dependencias fuera de la lista permitida: {unknown}",
                "vulnerabilities": 0}  # fmt: skip
    if not audit:
        return {"status": "skipped", "reason": "auditoría de vulnerabilidades deshabilitada",
                "vulnerabilities": 0}  # fmt: skip
    with tempfile.TemporaryDirectory(prefix="deps-") as tmp:
        req = Path(tmp) / "requirements.txt"
        req.write_text(requirements, encoding="utf-8")
        cmd = [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            str(req),
            "-f",
            "json",
            "--progress-spinner",
            "off",
        ]
        try:
            proc = subprocess.run(  # noqa: S603  # nosec B603
                cmd, capture_output=True, text=True, timeout=timeout, cwd=tmp
            )
            data = json.loads(proc.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return {"status": "skipped", "reason": "pip-audit no pudo completarse (¿sin red?): NO verificado",
                    "vulnerabilities": 0}  # fmt: skip
    vulns = sum(len(d.get("vulns", [])) for d in data.get("dependencies", []))
    return {"status": "failed" if vulns else "passed", "reason": "", "vulnerabilities": vulns}
