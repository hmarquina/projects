"""Pipeline de ingeniería: ejecución, aprobación humana y release package.

Segregación de funciones: quien ejecuta el pipeline (tech_lead) no aprueba (approver); un aprobador
tampoco puede haber creado la iniciativa, los artefactos, el análisis ni la ejecución. Aprobar exige
reconocer explícitamente los riesgos residuales. Ninguna salida de IA se aprueba a sí misma.
"""

import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit
from app.ai.gateway import ModelGateway, get_gateway
from app.db import get_db
from app.models import Approval, Artifact, Initiative, PipelineRun, Release
from app.pipeline import orchestrator, release
from app.pipeline.evidence import sha256
from app.routers.artifacts import _ready_analysis
from app.security import Principal, require

router = APIRouter(tags=["pipeline"])
REQUIRED = ("stories", "acceptance_criteria", "risks", "architecture", "api_contract")


class DecisionIn(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str = Field(min_length=5, max_length=1000)
    risk_acknowledged: bool = False


class PipelineRunOut(BaseModel):
    id: int
    initiative_id: int
    status: str
    steps: list[dict[str, Any]]
    readiness: dict[str, Any]
    traceability: list[dict[str, Any]]
    files: dict[str, str]
    evidence: dict[str, Any]
    evidence_ref: str
    created_by: str
    created_at: datetime
    approval: dict[str, Any] | None
    release_id: int | None


class ReleaseOut(BaseModel):
    id: int
    run_id: int
    version: str
    package_sha256: str
    manifest: dict[str, Any]
    created_by: str
    created_at: datetime


def _run_out(db: Session, row: PipelineRun) -> PipelineRunOut:
    appr = db.scalars(
        select(Approval).where(Approval.run_id == row.id).order_by(Approval.id.desc())
    ).first()
    rel = db.scalars(select(Release).where(Release.run_id == row.id)).first()
    return PipelineRunOut(
        id=row.id, initiative_id=row.initiative_id, status=row.status,
        steps=json.loads(row.steps_json), readiness=json.loads(row.readiness_json),
        traceability=json.loads(row.traceability_json), files=json.loads(row.file_hashes_json),
        evidence=json.loads(row.evidence_json),
        evidence_ref=row.evidence_ref, created_by=row.created_by, created_at=row.created_at,
        approval=None if appr is None else {
            "decision": appr.decision, "approver": appr.approver, "comment": appr.comment,
            "risk_acknowledged": bool(appr.risk_acknowledged), "at": appr.created_at.isoformat()},
        release_id=rel.id if rel else None,
    )  # fmt: skip


def _get_run(db: Session, run_id: int) -> PipelineRun:
    row = db.get(PipelineRun, run_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ejecución no encontrada")
    return row


@router.post("/initiatives/{initiative_id}/pipeline", response_model=PipelineRunOut,
             status_code=status.HTTP_201_CREATED)  # fmt: skip
def run_pipeline(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("pipeline:run"))],
    gateway: Annotated[ModelGateway, Depends(get_gateway)],
) -> PipelineRunOut:
    item = db.get(Initiative, initiative_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa no encontrada")
    analysis = _ready_analysis(db, item)
    ref = audit.content_ref(item.description)
    arts: dict[str, dict[str, Any]] = {}
    for kind in REQUIRED:
        art = db.scalars(
            select(Artifact).where(Artifact.initiative_id == initiative_id, Artifact.kind == kind,
                                   Artifact.requirement_ref == ref).order_by(Artifact.version.desc())
        ).first()  # fmt: skip
        if art is None:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Falta el artefacto vigente '{kind}': genere todos los artefactos primero")  # fmt: skip
        arts[kind] = {
            "meta": {"kind": kind, "id": art.id, "version": art.version, "model": art.model,
                     "prompt_label": art.prompt_label, "sha256": sha256(art.content_json)[:32]},
            "content": json.loads(art.content_json),
        }  # fmt: skip
    inp = orchestrator.Inputs(
        initiative={"id": item.id, "title": item.title},
        requirement_ref=ref,
        analysis={
            "id": analysis.id,
            "score": analysis.score,
            "prompt_label": analysis.prompt_label,
            "model": analysis.model,
        },  # fmt: skip
        artifacts=arts,
    )
    out = orchestrator.run(db, gateway, inp, who.username)
    creators = {item.created_by, analysis.created_by, who.username}
    creators |= {
        r
        for r in db.scalars(
            select(Artifact.created_by).where(Artifact.initiative_id == initiative_id)
        )
    }
    row = PipelineRun(
        initiative_id=initiative_id, requirement_ref=ref, status=out.status,
        steps_json=json.dumps(out.steps), files_json=json.dumps(out.files),
        file_hashes_json=json.dumps(out.file_hashes), traceability_json=json.dumps(out.trace),
        readiness_json=json.dumps(out.ready), evidence_json=json.dumps(out.evidence, ensure_ascii=False),
        evidence_ref=out.evidence_ref, contributors=json.dumps(sorted(creators)), created_by=who.username,
    )  # fmt: skip
    db.add(row)
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="pipeline.run",
        ai_model=out.ai_labels.get("model", ""), prompt_version=out.ai_labels.get("code_skeleton", ""),
        input_ref=ref, output_ref=out.evidence_ref, decision=out.status,
        resulting_artifact=f"run:{row.id}",
    )  # fmt: skip
    return _run_out(db, row)


@router.get("/initiatives/{initiative_id}/pipeline-runs", response_model=list[PipelineRunOut])
def list_runs(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> list[PipelineRunOut]:
    rows = db.scalars(
        select(PipelineRun)
        .where(PipelineRun.initiative_id == initiative_id)
        .order_by(PipelineRun.id)
    )
    return [_run_out(db, r) for r in rows]


@router.get("/pipeline-runs", response_model=list[PipelineRunOut])
def list_all_runs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
    status_filter: Annotated[
        Literal["blocked", "awaiting_approval", "approved", "rejected"] | None,
        Query(alias="status"),
    ] = None,
) -> list[PipelineRunOut]:
    query = select(PipelineRun).order_by(PipelineRun.id.desc())
    if status_filter:
        query = query.where(PipelineRun.status == status_filter)
    return [_run_out(db, r) for r in db.scalars(query)]


@router.get("/pipeline-runs/{run_id}", response_model=PipelineRunOut)
def get_run(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> PipelineRunOut:
    return _run_out(db, _get_run(db, run_id))


@router.get("/pipeline-runs/{run_id}/files/{path:path}")
def get_file(
    run_id: int, path: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> Response:  # fmt: skip
    files = json.loads(_get_run(db, run_id).files_json)
    if path not in files:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Archivo no encontrado")
    return Response(content=files[path], media_type="text/plain; charset=utf-8")


@router.post("/pipeline-runs/{run_id}/decision", response_model=PipelineRunOut)
def decide(
    run_id: int, body: DecisionIn,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("release:approve"))],
) -> PipelineRunOut:  # fmt: skip
    row = _get_run(db, run_id)
    if row.status != "awaiting_approval":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"La ejecución está '{row.status}'; no admite decisión"
        )
    if who.username in json.loads(row.contributors):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Segregación de funciones: no puede decidir quien creó este trabajo",
        )
    if body.decision == "approved" and not body.risk_acknowledged:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Aprobar exige reconocer los riesgos residuales"
        )
    db.add(Approval(run_id=run_id, decision=body.decision, approver=who.username,
                    comment=body.comment, risk_acknowledged=int(body.risk_acknowledged)))  # fmt: skip
    row.status = body.decision
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="pipeline.decision",
        approval=f"{body.decision}:{who.username}", decision=body.decision,
        input_ref=row.evidence_ref, resulting_artifact=f"run:{run_id}",
    )  # fmt: skip
    return _run_out(db, row)


def _release_out(row: Release) -> ReleaseOut:
    return ReleaseOut(id=row.id, run_id=row.run_id, version=row.version,
                      package_sha256=row.package_sha256, manifest=json.loads(row.manifest_json),
                      created_by=row.created_by, created_at=row.created_at)  # fmt: skip


@router.post(
    "/pipeline-runs/{run_id}/release",
    response_model=ReleaseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_release(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("release:create"))],
) -> ReleaseOut:
    row = _get_run(db, run_id)
    if row.status != "approved":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Solo se publica una ejecución aprobada por un humano"
        )
    if db.scalars(select(Release).where(Release.run_id == run_id)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta ejecución ya tiene release")
    files: dict[str, str] = json.loads(row.files_json)
    recorded: dict[str, str] = json.loads(row.file_hashes_json)
    if {p: sha256(c) for p, c in files.items()} != recorded:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Integridad: los archivos no coinciden con los hashes registrados",
        )
    appr = db.scalars(
        select(Approval).where(Approval.run_id == run_id, Approval.decision == "approved")
    ).one()
    evidence = json.loads(row.evidence_json)
    evidence["approval"] = {"approver": appr.approver, "comment": appr.comment,
                            "risk_acknowledged": True, "at": appr.created_at.isoformat()}  # fmt: skip
    evidence_text = json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    payload = {**files, "evidence.json": evidence_text}
    count = db.scalar(select(func.count(Release.id)).join(PipelineRun, PipelineRun.id == Release.run_id)
                      .where(PipelineRun.initiative_id == row.initiative_id)) or 0  # fmt: skip
    manifest = {
        "release": f"v{count + 1}", "run_id": run_id, "initiative_id": row.initiative_id,
        "requirement_ref": row.requirement_ref, "evidence_ref": row.evidence_ref,
        "approved_by": appr.approver, "approved_at": appr.created_at.isoformat(),
        "readiness": json.loads(row.readiness_json)["score"],
        "files": {p: sha256(c) for p, c in sorted(payload.items())},
        "created_at": datetime.now(UTC).isoformat(),
    }  # fmt: skip
    package = release.build_package(payload, manifest)
    pkg_hash = release.package_hash(package)
    rel = Release(run_id=run_id, version=manifest["release"], manifest_json=json.dumps(manifest),
                  package_sha256=pkg_hash, package=package, created_by=who.username)  # fmt: skip
    db.add(rel)
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="release.create",
        approval=f"approved:{appr.approver}", decision="published", input_ref=row.evidence_ref,
        output_ref=f"sha256:{pkg_hash[:32]}", resulting_artifact=f"release:{rel.id}",
    )  # fmt: skip
    return _release_out(rel)


@router.get("/releases", response_model=list[ReleaseOut])
def list_releases(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> list[ReleaseOut]:
    return [_release_out(r) for r in db.scalars(select(Release).order_by(Release.id.desc()))]


@router.get("/releases/{release_id}", response_model=ReleaseOut)
def get_release(
    release_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> ReleaseOut:
    rel = db.get(Release, release_id)
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Release no encontrado")
    return _release_out(rel)


@router.get("/releases/{release_id}/download")
def download_release(
    release_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> Response:
    rel = db.get(Release, release_id)
    if rel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Release no encontrado")
    return Response(content=rel.package, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="release-{rel.version}.zip"',
                             "X-Package-SHA256": rel.package_sha256})  # fmt: skip
