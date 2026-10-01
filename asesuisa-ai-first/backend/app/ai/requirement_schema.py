from pydantic import BaseModel, Field


class Ambiguity(BaseModel):
    term: str = Field(max_length=80)
    matched_text: str = Field(max_length=80)
    quote: str = Field(max_length=500)
    reason: str = Field(max_length=300)
    clarifying_question: str = Field(max_length=300)


class DimensionScore(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    weight: int = Field(ge=0, le=100)


class RequirementAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    rating: str
    ready: bool
    dimensions: list[DimensionScore]
    ambiguities: list[Ambiguity]
    missing: list[str]
