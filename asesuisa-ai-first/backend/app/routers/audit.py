from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db
from app.models import AuditEvent
from app.schemas import AuditOut, AuditVerifyOut
from app.security import Principal, require

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut])
def list_events(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("audit:read"))],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditEvent]:
    return list(db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)))


@router.get("/verify", response_model=AuditVerifyOut)
def verify(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("audit:read"))],
) -> AuditVerifyOut:
    intact, bad = audit.verify_chain(db)
    return AuditVerifyOut(intact=intact, first_tampered_id=bad)
