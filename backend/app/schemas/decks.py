from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class DeckCreate(BaseModel):
    title: str
    cert_id: Optional[int] = None
    custom_cert_name: Optional[str] = None

    @model_validator(mode="after")
    def exactly_one_cert_source(self) -> DeckCreate:
        has_cert = self.cert_id is not None
        has_custom = bool(self.custom_cert_name and self.custom_cert_name.strip())
        if has_cert and has_custom:
            raise ValueError("Provide cert_id or custom_cert_name, not both")
        return self


class DeckSummary(BaseModel):
    id: int
    title: str
    cert_id: Optional[int] = None
    custom_cert_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeckDetail(DeckSummary):
    cert_slug: Optional[str] = None
    cert_display_name: Optional[str] = None
    card_count: int = 0
