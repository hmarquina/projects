from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.requirement_schema import RequirementAnalysis


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    role: str


class InitiativeCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=10_000)


class InitiativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    created_by: str
    created_at: datetime


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: str
    user: str
    role: str
    action: str
    ai_model: str
    prompt_version: str
    input_ref: str
    output_ref: str
    approval: str
    decision: str
    resulting_artifact: str
    hash: str


class AuditVerifyOut(BaseModel):
    intact: bool
    first_tampered_id: int | None


class AnalysisOut(BaseModel):
    id: int
    initiative_id: int
    kind: str
    score: int
    ready: bool
    rating: str
    prompt_label: str
    model: str
    pii_redactions: dict[str, int]
    injection_flags: int
    result: RequirementAnalysis
    created_by: str
    created_at: datetime


class InitiativeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)


class ArtifactOut(BaseModel):
    id: int
    initiative_id: int
    kind: str
    version: int
    status: str
    prompt_label: str
    model: str
    analysis_id: int
    requirement_ref: str
    content: dict[str, Any]
    created_by: str
    created_at: datetime
