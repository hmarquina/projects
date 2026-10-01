from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash de relleno para igualar el tiempo de respuesta cuando el usuario no existe.
_DUMMY = hash_password("dummy-password-for-timing")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.scalars(select(User).where(User.username == body.username)).first()
    ok = verify_password(body.password, user.password_hash if user else _DUMMY)
    if not user or not ok:
        audit.record(db, user=body.username[:64], role="-", action="auth.login", decision="denied")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
    audit.record(db, user=user.username, role=user.role, action="auth.login", decision="granted")
    return TokenResponse(access_token=create_token(user.username, user.role), role=user.role)
