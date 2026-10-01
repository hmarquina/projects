from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db
from app.models import Initiative
from app.schemas import InitiativeCreate, InitiativeOut
from app.security import Principal, require

router = APIRouter(prefix="/initiatives", tags=["initiatives"])


@router.post("", response_model=InitiativeOut, status_code=status.HTTP_201_CREATED)
def create_initiative(
    body: InitiativeCreate,
    db: Annotated[Session, Depends(get_db)],
    who: Annotated[Principal, Depends(require("initiative:create"))],
) -> Initiative:
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
