from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Domain(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    weight_pct: int
    description: str


class CertificationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    display_name: str
    provider: str
    level: str
    pass_score_pct: int


class CertificationDetail(CertificationSummary):
    prompt_context: str
    domains: list[Domain]
