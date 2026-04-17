from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cards import Card, MCQOption
    from app.models.decks import Deck


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    score_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    deck: Mapped[Deck] = relationship("Deck")
    answers: Mapped[list[ExamAnswer]] = relationship(
        "ExamAnswer", back_populates="session", cascade="all, delete-orphan"
    )


class ExamAnswer(Base):
    __tablename__ = "exam_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("mcq_options.id", ondelete="SET NULL"), nullable=True
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[ExamSession] = relationship("ExamSession", back_populates="answers")
    card: Mapped[Card] = relationship("Card")
    selected_option: Mapped[MCQOption | None] = relationship("MCQOption")
