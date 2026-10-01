"""Autenticación (JWT) y autorización (RBAC).

El verificador de tokens está aislado en `decode_token` para poder sustituirlo por un
validador OIDC (JWKS) sin tocar los routers. Ver docs/DECISIONS.md.
"""

import hashlib
import hmac
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings

ROLES = ("viewer", "analyst", "tech_lead", "security", "approver", "admin")

# Segregación de funciones: quien genera artefactos no aprueba; quien aprueba no genera.
PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({"initiative:read"}),
    "analyst": frozenset(
        {"initiative:read", "initiative:create", "initiative:update", "ai:analyze", "ai:generate"}
    ),
    "tech_lead": frozenset({"initiative:read", "ai:analyze", "ai:generate", "pipeline:run"}),
    "security": frozenset({"initiative:read", "security:review", "audit:read"}),
    "approver": frozenset({"initiative:read", "release:approve", "audit:read"}),
    "admin": frozenset({"initiative:read", "audit:read", "user:manage"}),
}

_bearer = HTTPBearer(auto_error=False)


class Principal(BaseModel):
    username: str
    role: str


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    candidate = hash_password(password, bytes.fromhex(salt_hex)).split("$")[2]
    return hmac.compare_digest(candidate, digest_hex)


def create_token(username: str, role: str) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    claims = {
        "sub": username,
        "role": role,
        "iss": s.jwt_issuer,
        "iat": now,
        "exp": now + timedelta(minutes=s.jwt_ttl_minutes),
    }
    return jwt.encode(claims, s.require_jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> Principal:
    s = get_settings()
    try:
        data = jwt.decode(
            token,
            s.require_jwt_secret(),
            algorithms=["HS256"],
            issuer=s.jwt_issuer,
            options={"require": ["exp", "sub", "role", "iss"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido") from exc
    if data["role"] not in ROLES:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Rol desconocido")
    return Principal(username=data["sub"], role=data["role"])


def current_principal(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticación requerida")
    return decode_token(creds.credentials)


def require(permission: str) -> Callable[..., Principal]:
    def checker(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
        if permission not in PERMISSIONS.get(principal.role, frozenset()):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permiso insuficiente")
        return principal

    return checker
