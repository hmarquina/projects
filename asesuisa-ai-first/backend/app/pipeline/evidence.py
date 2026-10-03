"""Trazabilidad criterio→prueba, score de readiness y evidencia de cambio."""

import hashlib
import json
from typing import Any

from app.pipeline.docs import REQUIRED_SECTIONS

READINESS_THRESHOLD = 85


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def traceability(
    mapping: list[dict[str, Any]], tests: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    outcome = {t["name"]: t["outcome"] for t in tests}
    rows = []
    for m in mapping:
        results = [outcome.get(n, "missing") for n in m["tests"]]
        if m["kind"] == "manual" or not m["tests"]:
            status = "manual"
        elif all(r == "passed" for r in results):
            status = m["kind"]  # verified | smoke
        else:
            status = "failed"
        rows.append(
            {"ac_id": m["ac_id"], "tests": m["tests"], "status": status, "reason": m["reason"]}
        )
    return rows


# Puntos maximos por componente (suman 100). La UI los muestra en el desglose del bloqueo.
MAXIMUMS: dict[str, int] = {
    "calidad_requerimiento": 20,
    "pruebas": 25,
    "sast": 10,
    "secretos": 7,
    "dependencias": 8,
    "trazabilidad": 15,
    "documentacion": 5,
    "evidencia_completa": 10,
}


def readiness(
    *, analysis_score: int, tests: list[dict[str, Any]], bandit: dict[str, Any],
    secrets: dict[str, Any], deps: dict[str, Any], trace: list[dict[str, Any]],
    readme: str, evidence_complete: bool,
) -> dict[str, Any]:  # fmt: skip
    passed = sum(1 for t in tests if t["outcome"] == "passed")
    automated = sum(1 for r in trace if r["status"] in ("verified", "smoke"))
    comp = {
        "calidad_requerimiento": round(analysis_score * MAXIMUMS["calidad_requerimiento"] / 100, 1),
        "pruebas": round(MAXIMUMS["pruebas"] * passed / len(tests), 1) if tests else 0.0,
        "sast": MAXIMUMS["sast"] if bandit["status"] == "passed" else 0.0,
        "secretos": MAXIMUMS["secretos"] if secrets["ok"] else 0.0,
        "dependencias": MAXIMUMS["dependencias"] if deps["status"] == "passed" else 0.0,
        "trazabilidad": round(MAXIMUMS["trazabilidad"] * automated / len(trace), 1)
        if trace
        else 0.0,
        "documentacion": MAXIMUMS["documentacion"]
        if all(s in readme for s in REQUIRED_SECTIONS)
        else 0.0,
        "evidencia_completa": MAXIMUMS["evidencia_completa"] if evidence_complete else 0.0,
    }
    unverified = []
    if deps["status"] == "skipped":
        unverified.append(f"dependencias: {deps['reason']}")
    if bandit["status"] == "skipped":
        unverified.append(f"SAST: {bandit['reason']}")
    unverified += [f"{r['ac_id']}: requiere verificación manual/operativa"
                   for r in trace if r["status"] == "manual"]  # fmt: skip
    return {"score": round(sum(comp.values())), "threshold": READINESS_THRESHOLD,
            "components": comp, "maximums": dict(MAXIMUMS), "unverified": unverified}  # fmt: skip


def build_evidence(
    *, initiative: dict[str, Any], requirement_ref: str, analysis: dict[str, Any],
    artifacts: list[dict[str, Any]], file_hashes: dict[str, str], tests: list[dict[str, Any]],
    security: dict[str, Any], trace: list[dict[str, Any]], ready: dict[str, Any],
    steps: list[dict[str, Any]], run_by: str,
) -> dict[str, Any]:  # fmt: skip
    return {
        "schema": "change-evidence/1",
        "initiative": initiative,
        "requirement_ref": requirement_ref,
        "analysis": analysis,
        "ai_artifacts": artifacts,
        "ai_involvement": (
            "Artefactos y código generados con asistencia de IA en estado borrador; "
            "ninguna salida de IA se aprueba a sí misma: la aprobación es humana y auditada."
        ),
        "generated_files": file_hashes,
        "tests": {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["outcome"] == "passed"),
            "failed": sum(1 for t in tests if t["outcome"] == "failed"),
        },
        "security": security,
        "traceability": trace,
        "readiness": ready,
        "steps": [{k: s[k] for k in ("name", "status", "blocking", "detail")} for s in steps],
        "run_by": run_by,
    }


def evidence_ref(evidence: dict[str, Any]) -> str:
    return "sha256:" + sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=False))[:32]
