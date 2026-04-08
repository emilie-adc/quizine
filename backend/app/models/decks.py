from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cards import Card
    from app.models.certifications import Certification
    from app.models.ingest import SourceChunk


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cert_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("certifications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    custom_cert_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    certification: Mapped[Certification | None] = relationship(
        "Certification", back_populates="decks"
    )
    source_chunks: Mapped[list[SourceChunk]] = relationship(
        "SourceChunk", back_populates="deck", cascade="all, delete-orphan"
    )
    cards: Mapped[list[Card]] = relationship(
        "Card", back_populates="deck", cascade="all, delete-orphan"
    )
