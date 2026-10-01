import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.ai.gateway import GatewayError, ModelGateway, get_gateway
from app.ai.requirement_schema import RequirementAnalysis
from app.db import get_db
from app.models import Analysis, Initiative
from app.schemas import AnalysisOut
from app.security import Principal, require

router = APIRouter(prefix="/initiatives/{initiative_id}", tags=["ai-analysis"])


def _to_out(row: Analysis) -> AnalysisOut:
    result = RequirementAnalysis.model_validate_json(row.result_json)
    return AnalysisOut(
        id=row.id,
        initiative_id=row.initiative_id,
        kind=row.kind,
        score=row.score,
        ready=result.ready,
        rating=result.rating,
        prompt_label=row.prompt_label,
        model=row.model,
        pii_redactions=json.loads(row.pii_redactions or "{}"),
        injection_flags=row.injection_flags,
        result=result,
        created_by=row.created_by,
        created_at=row.created_at,
    )


@router.post("/analyze", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def analyze_requirement(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("ai:analyze"))],
    gateway: Annotated[ModelGateway, Depends(get_gateway)],
) -> AnalysisOut:
    item = db.get(Initiative, initiative_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa no encontrada")
    if not item.description.strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "La iniciativa no tiene requerimiento"
        )
    try:
        res = gateway.run("requirement_quality", item.description, RequirementAnalysis)
    except GatewayError as exc:
        audit.record(
            db, user=who.username, role=who.role, action="ai.requirement_analysis",
            decision="failed", resulting_artifact=f"initiative:{initiative_id}",
        )  # fmt: skip
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "El análisis de IA no está disponible"
        ) from exc
    row = Analysis(
        initiative_id=initiative_id,
        kind="requirement_quality",
        prompt_label=res.prompt_label,
        model=res.model,
        score=res.output.score,
        input_ref=audit.content_ref(item.description),
        result_json=res.output.model_dump_json(),
        pii_redactions=json.dumps(res.redactions),
        injection_flags=res.injection_flags,
        created_by=who.username,
    )
    db.add(row)
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="ai.requirement_analysis",
        ai_model=res.model, prompt_version=res.prompt_label,
        input_ref=res.input_ref, output_ref=res.output_ref,
        decision="injection_flagged" if res.injection_flags else "completed",
        resulting_artifact=f"analysis:{row.id}",
    )  # fmt: skip
    return _to_out(row)


@router.get("/analyses", response_model=list[AnalysisOut])
def list_analyses(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> list[AnalysisOut]:
    rows = db.scalars(
        select(Analysis).where(Analysis.initiative_id == initiative_id).order_by(Analysis.id)
    )
    return [_to_out(r) for r in rows]
