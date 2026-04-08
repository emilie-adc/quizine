"""
T11 model tests — use SQLite in-memory (synchronous) to validate schema
without requiring a running Postgres instance.
"""
from sqlalchemy import create_engine, inspect

from app.models import (
    Base,
    Card,
    CardReview,
    CardSchedule,
    CardTag,
    CertDomain,
    Certification,
    Deck,
    ExamAnswer,
    ExamSession,
    MCQOption,
    SourceChunk,
)

EXPECTED_TABLES = {
    "certifications",
    "cert_domains",
    "decks",
    "source_chunks",
    "cards",
    "mcq_options",
    "card_tags",
    "card_schedule",
    "card_reviews",
    "exam_sessions",
    "exam_answers",
}


def make_engine():
    return create_engine("sqlite:///:memory:")


def test_all_tables_created():
    engine = make_engine()
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES == tables


def test_certifications_columns():
    engine = make_engine()
    Base.metadata.create_all(engine)
    cols = {c["name"] for c in inspect(engine).get_columns("certifications")}
    assert {"id", "slug", "display_name", "provider", "level", "pass_score_pct",
            "verified", "prompt_context"} <= cols


def test_cert_domains_fk_to_certifications():
    engine = make_engine()
    Base.metadata.create_all(engine)
    fks = inspect(engine).get_foreign_keys("cert_domains")
    referred = {fk["referred_table"] for fk in fks}
    assert "certifications" in referred


def test_decks_nullable_cert_id():
    """cert_id must be nullable to support custom cert decks (ADR-005)."""
    cert_id_col = next(
        c for c in Deck.__table__.columns if c.name == "cert_id"
    )
    assert cert_id_col.nullable is True


def test_mcq_options_has_position():
    """Options store stable display position, not shuffled at query time (ADR-004)."""
    cols = {c.name for c in MCQOption.__table__.columns}
    assert "position" in cols


def test_card_schedule_unique_card_id():
    """card_schedule.card_id must be unique — one schedule per card (ADR-003)."""
    card_id_col = next(
        c for c in CardSchedule.__table__.columns if c.name == "card_id"
    )
    assert card_id_col.unique is True


def test_card_tags_composite_pk():
    """card_tags uses (card_id, domain_id) as composite PK (ADR-006)."""
    pk_cols = {c.name for c in CardTag.__table__.primary_key.columns}
    assert pk_cols == {"card_id", "domain_id"}


def test_no_user_id_anywhere():
    """No user_id columns on any table (ADR-001)."""
    engine = make_engine()
    Base.metadata.create_all(engine)
    insp = inspect(engine)
    for table in EXPECTED_TABLES:
        col_names = {c["name"] for c in insp.get_columns(table)}
        assert "user_id" not in col_names, f"user_id found on {table}"


def test_all_models_importable():
    """Smoke test that all model classes can be imported without error."""
    assert Certification.__tablename__ == "certifications"
    assert CertDomain.__tablename__ == "cert_domains"
    assert Deck.__tablename__ == "decks"
    assert SourceChunk.__tablename__ == "source_chunks"
    assert Card.__tablename__ == "cards"
    assert MCQOption.__tablename__ == "mcq_options"
    assert CardTag.__tablename__ == "card_tags"
    assert CardSchedule.__tablename__ == "card_schedule"
    assert CardReview.__tablename__ == "card_reviews"
    assert ExamSession.__tablename__ == "exam_sessions"
    assert ExamAnswer.__tablename__ == "exam_answers"
