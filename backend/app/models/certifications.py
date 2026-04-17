from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.decks import Deck


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    pass_score_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prompt_context: Mapped[str] = mapped_column(Text, nullable=False)

    domains: Mapped[list[CertDomain]] = relationship(
        "CertDomain", back_populates="certification", cascade="all, delete-orphan"
    )
    decks: Mapped[list[Deck]] = relationship("Deck", back_populates="certification")


class CertDomain(Base):
    __tablename__ = "cert_domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cert_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("certifications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    certification: Mapped[Certification] = relationship("Certification", back_populates="domains")
