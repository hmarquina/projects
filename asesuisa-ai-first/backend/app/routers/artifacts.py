"""Generación de artefactos de descubrimiento, protegida por la Definition of Ready.

Gate (AI Readiness Gate): solo se genera si existe un análisis del requerimiento VIGENTE
(mismo hash que el texto actual) y su score alcanza el umbral. Evita acelerar sobre una base mala.
"""

import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit
from app.ai.artifact_schemas import (
    AcceptanceOutput,
    ApiContractOutput,
    ArchitectureOutput,
    RisksOutput,
    StoriesOutput,
)
from app.ai.gateway import GatewayError, ModelGateway, get_gateway
from app.ai.requirement_schema import RequirementAnalysis
from app.db import get_db
from app.models import Analysis, Artifact, Initiative
from app.schemas import ArtifactOut
from app.security import Principal, require

router = APIRouter(prefix="/initiatives/{initiative_id}", tags=["artifacts"])

Kind = Literal["stories", "acceptance_criteria", "risks", "architecture", "api_contract"]
_KINDS: dict[str, tuple[str, type[BaseModel]]] = {
    "stories": ("user_stories", StoriesOutput),
    "acceptance_criteria": ("acceptance_criteria", AcceptanceOutput),
    "risks": ("risk_assessment", RisksOutput),
    "architecture": ("architecture_proposal", ArchitectureOutput),
    "api_contract": ("api_contract", ApiContractOutput),
}


def _out(row: Artifact) -> ArtifactOut:
    return ArtifactOut(
        id=row.id,
        initiative_id=row.initiative_id,
        kind=row.kind,
        version=row.version,
        status=row.status,
        prompt_label=row.prompt_label,
        model=row.model,
        analysis_id=row.analysis_id,
        requirement_ref=row.requirement_ref,
        content=json.loads(row.content_json),
        created_by=row.created_by,
        created_at=row.created_at,
    )


def _ready_analysis(db: Session, item: Initiative) -> Analysis:
    ref = audit.content_ref(item.description)
    last = db.scalars(
        select(Analysis)
        .where(Analysis.initiative_id == item.id, Analysis.kind == "requirement_quality")
        .order_by(Analysis.id.desc())
        .limit(1)
    ).first()
    if last is None or last.input_ref != ref:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Falta un análisis vigente del requerimiento (analice antes de generar)",
        )
    result = RequirementAnalysis.model_validate_json(last.result_json)
    if not result.ready:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"El requerimiento no cumple la Definition of Ready (score {result.score}); "
            "resuelva las ambigüedades y vuelva a analizar",
        )
    return last


@router.post("/artifacts/{kind}", response_model=ArtifactOut, status_code=status.HTTP_201_CREATED)
def generate_artifact(
    initiative_id: int,
    kind: Kind,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("ai:generate"))],
    gateway: Annotated[ModelGateway, Depends(get_gateway)],
) -> ArtifactOut:
    item = db.get(Initiative, initiative_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa no encontrada")
    analysis = _ready_analysis(db, item)
    prompt_id, schema = _KINDS[kind]
    try:
        res = gateway.run(prompt_id, item.description, schema)
    except GatewayError as exc:
        audit.record(
            db, user=who.username, role=who.role, action=f"ai.generate.{kind}",
            decision="failed", resulting_artifact=f"initiative:{initiative_id}",
        )  # fmt: skip
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "La generación de IA no está disponible"
        ) from exc
    version = (
        db.scalar(
            select(func.max(Artifact.version)).where(
                Artifact.initiative_id == initiative_id, Artifact.kind == kind
            )
        )
        or 0
    ) + 1
    row = Artifact(
        initiative_id=initiative_id,
        kind=kind,
        version=version,
        requirement_ref=analysis.input_ref,
        analysis_id=analysis.id,
        prompt_label=res.prompt_label,
        model=res.model,
        content_json=res.output.model_dump_json(),
        created_by=who.username,
    )
    db.add(row)
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action=f"ai.generate.{kind}",
        ai_model=res.model, prompt_version=res.prompt_label,
        input_ref=res.input_ref, output_ref=res.output_ref,
        decision="draft_created", resulting_artifact=f"artifact:{row.id}",
    )  # fmt: skip
    return _out(row)


@router.get("/artifacts", response_model=list[ArtifactOut])
def list_artifacts(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> list[ArtifactOut]:
    rows = db.scalars(
        select(Artifact).where(Artifact.initiative_id == initiative_id).order_by(Artifact.id)
    )
    return [_out(r) for r in rows]
