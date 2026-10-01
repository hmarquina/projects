from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.ai.guardrails import find_pii
from app.db import get_db
from app.models import Initiative
from app.schemas import InitiativeCreate, InitiativeOut, InitiativeUpdate
from app.security import Principal, require

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


@router.post("", response_model=InitiativeOut, status_code=status.HTTP_201_CREATED)
def create_initiative(
    body: InitiativeCreate,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("initiative:create"))],
) -> Initiative:
    if find_pii(body.title + "\n" + body.description):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "El texto contiene datos personales; use datos sintéticos o enmascarados",
        )
    item = Initiative(title=body.title, description=body.description, created_by=who.username)
    db.add(item)
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="initiative.create",
        input_ref=audit.content_ref(body.title + body.description),
        resulting_artifact=f"initiative:{item.id}",
    )  # fmt: skip
    return item


@router.get("", response_model=list[InitiativeOut])
def list_initiatives(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> list[Initiative]:
    return list(db.scalars(select(Initiative).order_by(Initiative.id)))


@router.get("/{initiative_id}", response_model=InitiativeOut)
def get_initiative(
    initiative_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Principal, Depends(require("initiative:read"))],
) -> Initiative:
    item = db.get(Initiative, initiative_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa no encontrada")
    return item


@router.patch("/{initiative_id}", response_model=InitiativeOut)
def update_initiative(
    initiative_id: int,
    body: InitiativeUpdate,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("initiative:update"))],
) -> Initiative:
    item = db.get(Initiative, initiative_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Iniciativa no encontrada")
    title = body.title if body.title is not None else item.title
    description = body.description if body.description is not None else item.description
    if find_pii(title + "\n" + description):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "El texto contiene datos personales; use datos sintéticos o enmascarados",
        )
    item.title, item.description, item.status = title, description, "registered"
    db.commit()
    audit.record(
        db, user=who.username, role=who.role, action="initiative.update",
        input_ref=audit.content_ref(title + description),
        resulting_artifact=f"initiative:{item.id}",
    )  # fmt: skip
    return item
