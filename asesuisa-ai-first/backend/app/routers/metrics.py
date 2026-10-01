"""Datos de la Control Tower. `current` de las métricas organizacionales es siempre None:
la plataforma no las mide; se llenan con datos reales del diagnóstico de 30 días."""

import json
from collections import Counter
from functools import lru_cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit, productivity
from app.db import get_db
from app.models import Analysis, Approval, Artifact, AuditEvent, Initiative, PipelineRun, Release
from app.security import Principal, require

router = APIRouter(prefix="/metrics", tags=["metrics"])

# key, etiqueta, unidad, baseline (caso), target base, target stretch, mejor=, confianza, fuente
_ORG: tuple[tuple[str, str, str, float, float, float, str, str, str], ...] = (
    ("lead_time", "Lead time", "semanas", 20, 12.5, 10, "down", "media", "Value stream mapping + timestamps"),
    ("rework", "Retrabajo y aclaraciones", "%", 25, 12, 8, "down", "media-baja", "Muestreo de tiempos + etiquetas"),
    ("automated_tests", "Pruebas automatizadas", "%", 10, 62, 75, "up", "alta", "Cobertura de casos en CI"),
    ("defect_escape", "Defectos detectados post-QA", "%", 12, 6, 4, "down", "media", "Defectos UAT/producción"),
    ("doc_returns", "Cambios con devolución documental", "%", 30, 8, 4, "down", "alta", "Comité de cambios"),
    ("releases", "Releases a producción", "por mes", 2, 8, 14, "up", "media", "Pipeline de despliegue"),
    ("change_failure", "Incidentes atribuibles a cambios", "%", 8, 5, 3, "down", "media", "Gestión de incidentes"),
    ("wip", "Iniciativas simultáneas (WIP)", "iniciativas", 8, 6, 5, "down", "alta", "Portafolio"),
)  # fmt: skip


@lru_cache(maxsize=1)
def _model_summary() -> dict[str, Any]:
    scenarios = {
        name: {"capacity": round(productivity.capacity(lv), 2),
               "value_capacity": round(productivity.value_capacity(lv), 2)}
        for name, lv in productivity.SCENARIOS.items()
    }  # fmt: skip
    sim = productivity.simulate()
    return {
        "scenarios": scenarios,
        "demand_growth": 1.5,
        "required_scope_removed_for_2x_base": round(productivity.required_scope_removed(2.0), 3),
        "simulation": {
            "value_median": round(sim["value_p50"], 2),
            "value_p10": round(sim["value_p10"], 2),
            "value_p90": round(sim["value_p90"], 2),
            "p_value_ge_1_3": round(sim["p_value_ge_1.3"], 2),
            "p_value_ge_1_5": round(sim["p_value_ge_1.5"], 2),
            "p_value_ge_2_0": round(sim["p_value_ge_2.0"], 2),
        },
        "note": "Supuestos del autor; 2× de valor es el techo de los rangos, no un valor esperado.",
    }


@router.get("/control-tower")
def control_tower(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> dict[str, Any]:
    organizational: list[dict[str, Any]] = [
        {"key": k, "label": label, "unit": unit, "baseline": base, "target_base": tb,
         "target_stretch": ts, "better": better, "current": None, "trend": [],
         "confidence": conf, "source": src, "status": "sin dato: requiere medición real"}
        for k, label, unit, base, tb, ts, better, conf, src in _ORG
    ]  # fmt: skip

    analyses = list(db.scalars(select(Analysis).order_by(Analysis.id)))
    scores = [a.score for a in analyses]
    ready = sum(1 for a in analyses if json.loads(a.result_json)["ready"])
    runs = list(db.scalars(select(PipelineRun).order_by(PipelineRun.id)))
    readiness = [json.loads(r.readiness_json)["score"] for r in runs]
    coverage = []
    for r in runs:
        trace = json.loads(r.traceability_json)
        if trace:
            coverage.append(
                100 * sum(1 for t in trace if t["status"] in ("verified", "smoke")) / len(trace)
            )
    by_kind = Counter(db.scalars(select(Artifact.kind)))
    intact, _bad = audit.verify_chain(db)

    def avg(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 1) if xs else None

    platform = {
        "initiatives": db.scalar(select(func.count(Initiative.id))) or 0,
        "analyses": len(analyses),
        "requirement_quality_avg": avg([float(s) for s in scores]),
        "requirement_quality_series": scores[-20:],
        "ready_rate": round(100 * ready / len(analyses), 1) if analyses else None,
        "ai_artifacts": dict(by_kind),
        "pipeline_runs": len(runs),
        "pipeline_blocked_rate": round(100 * sum(r.status == "blocked" for r in runs) / len(runs), 1) if runs else None,
        "readiness_avg": avg([float(x) for x in readiness]),
        "readiness_series": readiness[-20:],
        "automated_criteria_coverage": avg(coverage),
        "approvals": db.scalar(select(func.count(Approval.id)).where(Approval.decision == "approved")) or 0,
        "rejections": db.scalar(select(func.count(Approval.id)).where(Approval.decision == "rejected")) or 0,
        "releases": db.scalar(select(func.count(Release.id))) or 0,
        "audit_events": db.scalar(select(func.count(AuditEvent.id))) or 0,
        "audit_intact": intact,
    }  # fmt: skip
    return {
        "organizational": organizational,
        "platform": platform,
        "model": _model_summary(),
        "disclaimer": "Las métricas organizacionales no tienen dato: el caso solo aporta el baseline. "
        "Las de plataforma miden el uso de este MVP con datos sintéticos.",
    }
