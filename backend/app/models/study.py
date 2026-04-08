from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cards import Card


class CardSchedule(Base):
    """Current SM-2 state for a card. Mutable — updated on every review."""
    __tablename__ = "card_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    interval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    card: Mapped[Card] = relationship("Card", back_populates="schedule")


class CardReview(Base):
    """Append-only review log. Never updated, per ADR-003."""
    __tablename__ = "card_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grade: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–5 SM-2 grade
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    card: Mapped[Card] = relationship("Card", back_populates="reviews")
