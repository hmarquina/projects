"""Orquesta el pipeline: generación → política → pruebas → seguridad → docs → evidencia → readiness.

Cada paso registra estado, si es bloqueante y su detalle. Lo que no pudo verificarse se marca
`skipped` (nunca `passed`) y baja el score de readiness.
"""

import json
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app import audit
from app.ai.gateway import GatewayError, ModelGateway
from app.config import get_settings
from app.pipeline import docs, evidence, policy, sandbox, security_checks
from app.pipeline.schemas import CodeBundle, TestBundle

MAX_FILES, MAX_FILE_BYTES = 30, 200_000
_ALLOWED_EXT = (".py", ".json", ".txt", ".ini")


@dataclass
class Inputs:
    initiative: dict[str, Any]
    requirement_ref: str
    analysis: dict[str, Any]
    artifacts: dict[str, dict[str, Any]]  # kind → {"meta": {...}, "content": {...}}


@dataclass
class Outcome:
    status: str
    steps: list[dict[str, Any]]
    files: dict[str, str]
    file_hashes: dict[str, str]
    trace: list[dict[str, Any]]
    ready: dict[str, Any]
    evidence: dict[str, Any]
    evidence_ref: str
    ai_labels: dict[str, str]


def _step(name: str, status: str, detail: str, blocking: bool, started: float) -> dict[str, Any]:
    return {"name": name, "status": status, "blocking": blocking, "detail": detail,
            "duration_ms": round((time.perf_counter() - started) * 1000)}  # fmt: skip


def validate_bundle(files: dict[str, str]) -> list[str]:
    problems = []
    if not files or len(files) > MAX_FILES:
        problems.append(f"cantidad de archivos inválida ({len(files)})")
    for path, content in files.items():
        if path.startswith("/") or ".." in path.split("/") or not path.endswith(_ALLOWED_EXT):
            problems.append(f"ruta o extensión no permitida: {path}")
        if len(content.encode()) > MAX_FILE_BYTES:
            problems.append(f"archivo demasiado grande: {path}")
    return problems


def run(db: Session, gateway: ModelGateway, inp: Inputs, run_by: str) -> Outcome:
    settings = get_settings()
    steps: list[dict[str, Any]] = []
    spec = inp.artifacts["api_contract"]["content"]["openapi"]
    criteria = inp.artifacts["acceptance_criteria"]["content"]["criteria"]
    payload = json.dumps({"openapi": spec, "criteria": criteria}, ensure_ascii=False)
    labels: dict[str, str] = {}
    files: dict[str, str] = {}
    mapping: list[dict[str, Any]] = []

    t = time.perf_counter()
    try:
        code = gateway.run("code_skeleton", payload, CodeBundle)
        tests_gen = gateway.run("test_generation", payload, TestBundle)
        labels = {"code_skeleton": code.prompt_label, "test_generation": tests_gen.prompt_label,
                  "model": code.model}  # fmt: skip
        files = {**code.output.files, **tests_gen.output.files}
        mapping = [m.model_dump() for m in tests_gen.output.mapping]
        steps.append(_step("generacion_ia", "passed",
                           f"{len(files)} archivos con {code.model}", True, t))  # fmt: skip
    except GatewayError as exc:
        steps.append(_step("generacion_ia", "failed", f"gateway: {exc}", True, t))

    t = time.perf_counter()
    problems = validate_bundle(files) if files else ["sin archivos generados"]
    steps.append(_step("validacion_bundle", "failed" if problems else "passed",
                       "; ".join(problems) or "rutas, extensiones y tamaños válidos", True, t))  # fmt: skip

    t = time.perf_counter()
    violations = [] if problems else policy.check_files(files)
    gate_open = not problems and not violations
    steps.append(_step(
        "politica_estatica", "failed" if violations else ("passed" if gate_open else "skipped"),
        "; ".join(f"{v.file}:{v.line} {v.rule}" for v in violations[:5])
        or ("imports, llamadas y atributos dentro de la política" if gate_open else "bundle inválido"),
        True, t,
    ))  # fmt: skip

    test_results: list[dict[str, Any]] = []
    t = time.perf_counter()
    if gate_open:
        res = sandbox.run_tests(files, settings.pipeline_timeout_seconds)
        test_results = res["tests"]
        n_ok = sum(1 for x in test_results if x["outcome"] == "passed")
        steps.append(_step("pruebas", "passed" if res["ok"] else "failed",
                           f"{n_ok}/{len(test_results)} pruebas pasaron {res['reason']}".strip(), True, t))  # fmt: skip
    else:
        steps.append(
            _step("pruebas", "skipped", "código no ejecutado: bloqueado por política", True, t)
        )

    skipped: dict[str, Any] = {"status": "skipped", "reason": "código bloqueado por política", "high": 0,
               "medium": 0, "low": 0, "vulnerabilities": 0}  # fmt: skip
    t = time.perf_counter()
    bandit: dict[str, Any] = security_checks.run_bandit(files) if gate_open else skipped
    steps.append(_step("sast_bandit", bandit["status"],
                       f"alta={bandit['high']} media={bandit['medium']} baja={bandit['low']}"
                       + (f" ({bandit['reason']})" if bandit["status"] == "skipped" else ""),
                       True, t))  # fmt: skip
    t = time.perf_counter()
    secrets: dict[str, Any] = security_checks.scan_secrets(files) if files else {"ok": False, "findings": [],
                                                                 "env_sourced": False}  # fmt: skip
    steps.append(_step("escaneo_secretos", "passed" if secrets["ok"] else "failed",
                       f"hallazgos={len(secrets['findings'])} credencial_desde_entorno={secrets['env_sourced']}",
                       True, t))  # fmt: skip
    t = time.perf_counter()
    deps: dict[str, Any] = security_checks.check_dependencies(files.get("requirements.txt", ""),
                                              settings.pipeline_dependency_audit) if gate_open else skipped  # fmt: skip
    steps.append(_step("dependencias", deps["status"], deps.get("reason") or f"vulnerabilidades={deps['vulnerabilities']}", True, t))  # fmt: skip

    t = time.perf_counter()
    trace = evidence.traceability(mapping, test_results)
    coverage = {r["ac_id"]: r["status"] for r in trace}
    readme = docs.generate_readme(
        inp.initiative["title"], spec, inp.artifacts["stories"]["content"], criteria,
        coverage, inp.artifacts["risks"]["content"]["risks"],
    )  # fmt: skip
    steps.append(
        _step("documentacion", "passed", "README generado desde artefactos (plantilla)", False, t)
    )
    n_auto = sum(1 for r in trace if r["status"] in ("verified", "smoke"))
    steps.append(_step("trazabilidad", "failed" if any(r["status"] == "failed" for r in trace) else "passed",
                       f"{n_auto}/{len(trace)} criterios con prueba automática que pasa", True, time.perf_counter()))  # fmt: skip

    all_files = {**files, "docs/README.md": readme}
    file_hashes = {p: evidence.sha256(c) for p, c in sorted(all_files.items())}
    intact, _ = audit.verify_chain(db)
    complete = (set(inp.artifacts) >= {"stories", "acceptance_criteria", "risks", "architecture", "api_contract"}
                and all(a["meta"]["model"] and a["meta"]["prompt_label"] for a in inp.artifacts.values()) and intact)  # fmt: skip
    ready = evidence.readiness(
        analysis_score=inp.analysis["score"], tests=test_results, bandit=bandit, secrets=secrets,
        deps=deps, trace=trace, readme=readme, evidence_complete=complete,
    )  # fmt: skip
    security = {"bandit": bandit, "secrets": secrets, "dependencies": deps}
    ev = evidence.build_evidence(
        initiative=inp.initiative, requirement_ref=inp.requirement_ref, analysis=inp.analysis,
        artifacts=[a["meta"] for a in inp.artifacts.values()], file_hashes=file_hashes,
        tests=test_results, security=security, trace=trace, ready=ready, steps=steps, run_by=run_by,
    )  # fmt: skip
    blocked = any(s["blocking"] and s["status"] == "failed" for s in steps)
    # una prueba bloqueada por política cuenta como bloqueo aunque figure `skipped`
    blocked = blocked or any(s["name"] == "pruebas" and s["status"] != "passed" for s in steps)
    status = "blocked" if blocked or ready["score"] < ready["threshold"] else "awaiting_approval"
    return Outcome(
        status, steps, all_files, file_hashes, trace, ready, ev, evidence.evidence_ref(ev), labels
    )
