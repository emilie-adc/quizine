from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.certifications import CertDomain
    from app.models.decks import Deck
    from app.models.ingest import SourceChunk
    from app.models.study import CardReview, CardSchedule


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_chunk_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("source_chunks.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "flashcard" | "mcq"
    front: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    back: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_topic_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    deck: Mapped[Deck] = relationship("Deck", back_populates="cards")
    source_chunk: Mapped[SourceChunk | None] = relationship("SourceChunk")
    mcq_options: Mapped[list[MCQOption]] = relationship(
        "MCQOption", back_populates="card", cascade="all, delete-orphan",
        order_by="MCQOption.position"
    )
    schedule: Mapped[CardSchedule | None] = relationship(
        "CardSchedule", back_populates="card", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[list[CardReview]] = relationship(
        "CardReview", back_populates="card", cascade="all, delete-orphan"
    )
    tags: Mapped[list[CardTag]] = relationship(
        "CardTag", back_populates="card", cascade="all, delete-orphan"
    )


class MCQOption(Base):
    __tablename__ = "mcq_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–3, per ADR-004
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    card: Mapped[Card] = relationship("Card", back_populates="mcq_options")


class CardTag(Base):
    __tablename__ = "card_tags"

    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True
    )
    domain_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cert_domains.id", ondelete="CASCADE"), primary_key=True
    )

    card: Mapped[Card] = relationship("Card", back_populates="tags")
    domain: Mapped[CertDomain] = relationship("CertDomain")
