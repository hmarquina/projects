"""Audit trail append-only con hash encadenado (detecta alteraciones)."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent

_HASH_FIELDS = (
    "timestamp", "user", "role", "action", "ai_model", "prompt_version", "input_ref",
    "output_ref", "approval", "decision", "resulting_artifact", "prev_hash",
)  # fmt: skip


def content_ref(content: str) -> str:
    """Referencia no reversible al contenido: se audita el hash, no el dato."""
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()[:32]


def _digest(event: AuditEvent) -> str:
    payload = {f: getattr(event, f) for f in _HASH_FIELDS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def record(db: Session, *, user: str, role: str, action: str, **fields: Any) -> AuditEvent:
    last = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1)).first()
    # Todos los campos hasheados se fijan explícitamente: si se dejaran a los defaults de la
    # columna, el hash se calcularía con None y la verificación posterior con "".
    values: dict[str, Any] = {f: "" for f in _HASH_FIELDS}
    values.update(
        timestamp=datetime.now(timezone.utc).isoformat(),
        user=user,
        role=role,
        action=action,
        prev_hash=last.hash if last else "",
    )
    values.update(fields)
    event = AuditEvent(**values)
    event.hash = _digest(event)
    db.add(event)
    db.commit()
    return event


def verify_chain(db: Session) -> tuple[bool, int | None]:
    """Devuelve (íntegra, id del primer evento alterado)."""
    prev = ""
    for event in db.scalars(select(AuditEvent).order_by(AuditEvent.id)):
        if event.prev_hash != prev or event.hash != _digest(event):
            return False, event.id
        prev = event.hash
    return True, None
