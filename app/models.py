"""Pydantic schema for the Examiner's JSON (source of truth: prompts/examiner.md)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ConceptScore(BaseModel):
    id: str
    score: int
    evidence: str = ""

    @field_validator("score")
    @classmethod
    def clamp(cls, v: int) -> int:
        return max(0, min(3, int(v)))


class Misconception(BaseModel):
    concept_id: str | None = None
    misconception_id: str | None = None
    description: str = ""
    not_in_graph: bool = False


class Flag(BaseModel):
    concept_id: str
    reason: str


class Probe(BaseModel):
    concept_id: str | None = None
    question_idea: str = ""
    planted_misconception_id: str | None = None
    planted_misconception: str | None = None
    ask_peer: str | None = None


class ExaminerOutput(BaseModel):
    concepts_touched: list[ConceptScore] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    struggling_concept_id: str | None = None
    flag_for_lecturer: Flag | None = None
    asked_for_answer: bool = False
    next_probe: Probe | None = None
