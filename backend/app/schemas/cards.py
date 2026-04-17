from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    custom_topic_tag: Optional[str] = None


class CardResponse(BaseModel):
    id: int
    deck_id: int
    type: str
    front: Optional[str] = None
    back: Optional[str] = None
    custom_topic_tag: Optional[str] = None
    approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}
