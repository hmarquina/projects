from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(32))


class Initiative(Base):
    __tablename__ = "initiatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="registered")
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Analysis(Base):
    """Resultado de un análisis de IA. Contiene texto ya redactado (sin PII)."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    initiative_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    prompt_label: Mapped[str] = mapped_column(String(96))
    model: Mapped[str] = mapped_column(String(64))
    score: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[str] = mapped_column(Text)
    input_ref: Mapped[str] = mapped_column(String(128), default="")
    pii_redactions: Mapped[str] = mapped_column(String(200), default="")
    injection_flags: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Artifact(Base):
    """Artefacto generado por IA. Nace en `draft`: requiere revisión humana (Fase 4)."""

    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    initiative_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    requirement_ref: Mapped[str] = mapped_column(String(128))
    analysis_id: Mapped[int] = mapped_column(Integer)
    prompt_label: Mapped[str] = mapped_column(String(96))
    model: Mapped[str] = mapped_column(String(64))
    content_json: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PipelineRun(Base):
    """Ejecución del pipeline sobre artefactos vigentes. Guarda archivos generados y evidencia."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    initiative_id: Mapped[int] = mapped_column(Integer, index=True)
    requirement_ref: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(24)
    )  # blocked | awaiting_approval | approved | rejected
    steps_json: Mapped[str] = mapped_column(Text)
    files_json: Mapped[str] = mapped_column(Text)
    file_hashes_json: Mapped[str] = mapped_column(Text)
    traceability_json: Mapped[str] = mapped_column(Text)
    readiness_json: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str] = mapped_column(Text)
    evidence_ref: Mapped[str] = mapped_column(String(128))
    contributors: Mapped[str] = mapped_column(Text)  # JSON: usuarios que crearon algo (segregación)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, index=True)
    decision: Mapped[str] = mapped_column(String(16))
    approver: Mapped[str] = mapped_column(String(64))
    comment: Mapped[str] = mapped_column(String(1000))
    risk_acknowledged: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, unique=True)
    version: Mapped[str] = mapped_column(String(16))
    manifest_json: Mapped[str] = mapped_column(Text)
    package_sha256: Mapped[str] = mapped_column(String(64))
    package: Mapped[bytes] = mapped_column(LargeBinary)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    """Registro append-only con hash encadenado. Guarda referencias (hash), no contenido."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(40))
    user: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(64), index=True)
    ai_model: Mapped[str] = mapped_column(String(64), default="")
    prompt_version: Mapped[str] = mapped_column(String(64), default="")
    input_ref: Mapped[str] = mapped_column(String(128), default="")
    output_ref: Mapped[str] = mapped_column(String(128), default="")
    approval: Mapped[str] = mapped_column(String(64), default="")
    decision: Mapped[str] = mapped_column(String(64), default="")
    resulting_artifact: Mapped[str] = mapped_column(String(128), default="")
    prev_hash: Mapped[str] = mapped_column(String(64), default="")
    hash: Mapped[str] = mapped_column(String(64), default="")


__all__ = [
    "Analysis",
    "Approval",
    "Artifact",
    "AuditEvent",
    "Initiative",
    "PipelineRun",
    "Release",
    "User",
]
