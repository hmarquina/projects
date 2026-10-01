from typing import Literal

from pydantic import BaseModel


class CodeBundle(BaseModel):
    files: dict[str, str]


class AcMapping(BaseModel):
    ac_id: str
    tests: list[str]
    kind: Literal["verified", "smoke", "manual"]
    reason: str


class TestBundle(BaseModel):
    __test__ = False  # evita que pytest lo tome por una clase de test

    files: dict[str, str]
    mapping: list[AcMapping]
