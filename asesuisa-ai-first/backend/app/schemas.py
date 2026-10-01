from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
