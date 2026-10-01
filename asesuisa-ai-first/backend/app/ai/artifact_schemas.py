"""Esquemas de los artefactos de descubrimiento. Todo artefacto es trazable a una cita literal."""

from typing import Any, Literal

from pydantic import BaseModel, Field

Level = Literal["low", "medium", "high"]


class UserStory(BaseModel):
    id: str
    actor: str
    want: str
    benefit: str
    benefit_confirmed: bool
    source_quote: str


class SystemRequirement(BaseModel):
    id: str
    text: str
    source_quote: str


class StoriesOutput(BaseModel):
    stories: list[UserStory]
    system_requirements: list[SystemRequirement]


class AcceptanceCriterion(BaseModel):
    id: str
    story_id: str
    origin: Literal["requirement", "baseline_control"]
    given: str
    when: str
    then: str
    measurable_constraints: list[str]
    source_quote: str


class AcceptanceOutput(BaseModel):
    criteria: list[AcceptanceCriterion]


class Risk(BaseModel):
    id: str
    category: str
    description: str
    likelihood: Level
    impact: Level
    severity: int = Field(ge=1, le=9)
    controls: list[str]
    evidence: str
    origin: Literal["signal", "baseline"]
    owner_role: str


class RisksOutput(BaseModel):
    risks: list[Risk]


class Component(BaseModel):
    name: str
    kind: str
    responsibility: str


class Relation(BaseModel):
    source: str
    target: str
    protocol: str


class Decision(BaseModel):
    decision: str
    rationale: str
    alternatives: str


class ArchitectureOutput(BaseModel):
    components: list[Component]
    relations: list[Relation]
    decisions: list[Decision]
    nfr: list[str]
    assumptions: list[str]


class ApiContractOutput(BaseModel):
    summary: str
    openapi: dict[str, Any]
